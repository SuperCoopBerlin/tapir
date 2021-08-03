from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from tapir import utils
from tapir.accounts import validators
from tapir.accounts.models import TapirUser
from tapir.coop import pdfs
from tapir.log.models import UpdateModelLogEntry, ModelLogEntry
from tapir.utils.models import DurationModelMixin, CountryField
from tapir.utils.user_utils import UserUtils

COOP_SHARE_PRICE = Decimal(100)
COOP_ENTRY_AMOUNT = Decimal(10)


class ShareOwner(models.Model):
    """ShareOwner represents an owner of a ShareOwnership.

    Usually, this is just a proxy for the associated user. However, it may also be used to
    represent a person or company that does not have their own account.
    """

    # Only for owners that have a user account
    user = models.OneToOneField(
        TapirUser,
        related_name="share_owner",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    is_company = models.BooleanField(
        verbose_name=_("Is company"), default=False, blank=False
    )
    company_name = models.CharField(max_length=150, blank=True)

    # In the case that this is a company, this is the contact data for the company representative
    # There can also be investing members that do not have a user account
    first_name = models.CharField(_("First name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    phone_number = PhoneNumberField(_("Phone Number"), blank=True)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")

    preferred_language = models.CharField(
        _("Preferred Language"),
        choices=utils.models.PREFERRED_LANGUAGES,
        default="de",
        max_length=16,
        blank=True,
    )

    is_investing = models.BooleanField(
        verbose_name=_("Is investing member"), default=False
    )

    ratenzahlung = models.BooleanField(verbose_name=_("Ratenzahlung"), default=False)

    # TODO(Leon Handreke): Remove this temporary field again after the Startnext member integration is done
    # It's only used to send special emails to these members
    from_startnext = models.BooleanField(default=False)

    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )

    class ShareOwnerQuerySet(models.QuerySet):
        def with_name(self, search_string: str):
            searches = [s for s in search_string.split(" ") if s != ""]

            combined_filters = Q(last_name__icontains="")
            for search in searches:
                word_filter = (
                    Q(last_name__unaccent__icontains=search)
                    | Q(first_name__unaccent__icontains=search)
                    | Q(user__first_name__unaccent__icontains=search)
                    | Q(user__last_name__unaccent__icontains=search)
                    | Q(company_name__unaccent__icontains=search)
                )
                combined_filters = combined_filters & word_filter

            return self.filter(combined_filters)

        def with_status(self, status: str):
            active_ownerships = ShareOwnership.objects.active_temporal()

            if status == MemberStatus.SOLD:
                return self.exclude(share_ownerships__in=active_ownerships)
            else:
                return self.filter(
                    share_ownerships__in=active_ownerships,
                    is_investing=(status == MemberStatus.INVESTING),
                )

    objects = ShareOwnerQuerySet.as_manager()

    def blank_info_fields(self):
        """Used after a ShareOwner is linked to a user, which is used as the source for user info instead."""
        self.first_name = ""
        self.last_name = ""
        self.email = ""
        self.birthdate = None
        self.street = ""
        self.street_2 = ""
        self.postcode = ""
        self.city = ""
        self.country = ""
        self.preferred_language = ""

    def clean(self):
        r = super().clean()
        if self.is_company and self.user:
            raise ValidationError(
                _("Cannot be a company share owner and have an associated user")
            )

        if self.user and (
            self.first_name
            or self.last_name
            or self.email
            or self.birthdate
            or self.street
            or self.street_2
            or self.postcode
            or self.city
            or self.country
            or self.preferred_language
        ):
            raise ValidationError(_("User info should be stored in associated user"))
        return r

    def get_display_name(self):
        if self.is_company:
            return self.company_name
        return UserUtils.build_display_name(self.first_name, self.last_name)

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def get_info(self):
        return self.user if self.user else self

    def get_absolute_url(self):
        if self.user:
            return self.user.get_absolute_url()
        return reverse("coop:shareowner_detail", args=[self.pk])

    def get_oldest_active_share_ownership(self):
        return self.get_active_share_ownerships().order_by("start_date").first()

    def get_active_share_ownerships(self):
        return self.share_ownerships.active_temporal()

    def num_shares(self) -> int:
        return ShareOwnership.objects.active_temporal().filter(owner=self).count()

    def get_member_status(self):
        oldest_active = self.get_oldest_active_share_ownership()
        if oldest_active is None or not oldest_active.is_active:
            return MemberStatus.SOLD

        if self.is_investing:
            return MemberStatus.INVESTING

        return MemberStatus.ACTIVE


class MemberStatus:
    SOLD = "sold"
    INVESTING = "investing"
    ACTIVE = "active"


MEMBER_STATUS_CHOICES = (
    (MemberStatus.SOLD, _("Sold")),
    (MemberStatus.INVESTING, _("Investing")),
    (MemberStatus.ACTIVE, _("Active")),
)


def get_member_status_translation(searched_status: str) -> str:
    for status in MEMBER_STATUS_CHOICES:
        if searched_status == status[0]:
            return status[1]


class UpdateShareOwnerLogEntry(UpdateModelLogEntry):
    template_name = "coop/log/update_share_owner_log_entry.html"


class ShareOwnership(DurationModelMixin, models.Model):
    """ShareOwnership represents ownership of a single share."""

    owner = models.ForeignKey(
        ShareOwner,
        related_name="share_ownerships",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )


class DeleteShareOwnershipLogEntry(ModelLogEntry):
    template_name = "coop/log/delete_share_ownership_log_entry.html"
    exclude_fields = ["id", "owner"]


class DraftUser(models.Model):
    username_validator = validators.UsernameValidator

    username = models.CharField(
        _("username"),
        max_length=150,
        validators=[username_validator],
    )
    first_name = models.CharField(_("First name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    phone_number = PhoneNumberField(_("Phone Number"), blank=True)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")

    preferred_language = models.CharField(
        _("Preferred Language"),
        choices=utils.models.PREFERRED_LANGUAGES,
        default="de",
        max_length=16,
    )

    # For now, make this not editable, as one is the 99%-case. In case somebody wants to buy more shares,
    # we should build a flow for existing users. This also solves the issue of keeping the invoice in sync.
    num_shares = models.IntegerField(
        _("Number of Shares"), blank=False, editable=False, default=1
    )

    is_investing = models.BooleanField(
        verbose_name=_("Investing member"), default=False
    )
    # TODO(Leon Handreke): Remove this temporary field again after the Startnext member integration is done
    # It's only used to send special emails to these members
    from_startnext = models.BooleanField(default=False)
    startnext_welcome_email_sent = models.BooleanField(default=False)

    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    signed_membership_agreement = models.BooleanField(
        _("Signed Beteiligungserklärung"), default=False
    )
    paid_membership_fee = models.BooleanField(_("Paid Membership Fee"), default=False)

    ratenzahlung = models.BooleanField(verbose_name=_("Ratenzahlung"), default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse(
            "coop:draftuser_detail",
            args=[
                self.pk,
            ],
        )

    def get_initial_amount(self):
        return self.num_shares * COOP_SHARE_PRICE + COOP_ENTRY_AMOUNT

    def get_display_name(self):
        return UserUtils.build_display_name(self.first_name, self.last_name)

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def can_create_user(self):
        return (
            self.email
            and self.username
            and self.first_name
            and self.last_name
            and self.signed_membership_agreement
        )

    def send_startnext_email(self):
        if not self.from_startnext:
            raise Exception("Not from startnext")
        if self.startnext_welcome_email_sent:
            print(
                "Welcome email for %d %s already sent"
                % (self.pk, self.get_display_name())
            )
            return

        mail = EmailMessage(
            subject=_("Willkommen bei SuperCoop eG!"),
            body=render_to_string(
                "coop/email/membership_agreement_startnext.html", {"u": self}
            ),
            from_email="SuperCoop Berlin eG <mitglied@supercoop.de>",
            to=[self.email],
            bcc=["mitglied@supercoop.de"],
            attachments=[
                (
                    "Beteiligungserklärung %s.pdf" % self.get_display_name(),
                    pdfs.get_membership_agreement_pdf(self).write_pdf(),
                    "application/pdf",
                )
            ],
        )
        mail.content_subtype = "html"
        mail.send()

        self.startnext_welcome_email_sent = True
        self.save()

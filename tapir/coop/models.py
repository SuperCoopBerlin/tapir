from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from tapir import utils
from tapir.accounts.models import TapirUser
from tapir.coop.config import COOP_SHARE_PRICE, COOP_ENTRY_AMOUNT
from tapir.log.models import UpdateModelLogEntry, ModelLogEntry
from tapir.utils.models import (
    DurationModelMixin,
    CountryField,
)
from tapir.utils.user_utils import UserUtils


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
    phone_number = PhoneNumberField(_("Phone number"), blank=True)
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
    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    paid_membership_fee = models.BooleanField(_("Paid Entrance Fee"), default=True)
    willing_to_gift_a_share = models.DateField(
        _("Is willing to gift a share"), null=True, blank=True
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
                ).distinct()

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
        self.phone_number = ""

    def clean(self):
        r = super().clean()
        if self.is_company and self.user:
            raise ValidationError(_("Cannot be a company and have a Tapir account"))

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
            or self.phone_number
        ):
            raise ValidationError(
                _("User info should be stored in associated Tapir account")
            )
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

    def can_shop(self):
        return (
            self.user is not None
            and self.user.shift_user_data.is_balance_ok()
            and self.is_active()
        )

    def is_active(self) -> bool:
        return self.get_member_status() == MemberStatus.ACTIVE

    def get_total_expected_payment(self) -> float:
        return COOP_ENTRY_AMOUNT + self.share_ownerships.count() * COOP_SHARE_PRICE

    def get_currently_paid_amount(self) -> float:
        return (
            IncomingPayment.objects.filter(credited_member=self).aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )


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

    amount_paid = models.DecimalField(
        blank=False,
        null=False,
        default=COOP_SHARE_PRICE,
        max_digits=10,
        decimal_places=2,
    )

    def is_fully_paid(self):
        return self.amount_paid >= COOP_SHARE_PRICE

    def clean(self):
        super().clean()
        if self.amount_paid < 0:
            raise ValidationError(_("Amount paid for a share can't be negative"))
        if self.amount_paid > COOP_SHARE_PRICE:
            raise ValidationError(
                _(
                    f"Amount paid for a share can't more than {COOP_SHARE_PRICE} (the price of a share)"
                )
            )


class DeleteShareOwnershipLogEntry(ModelLogEntry):
    template_name = "coop/log/delete_share_ownership_log_entry.html"
    exclude_fields = ["id", "owner"]


class DraftUser(models.Model):
    first_name = models.CharField(_("First name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    phone_number = PhoneNumberField(_("Phone number"), blank=True)
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

    num_shares = models.IntegerField(_("Number of Shares"), blank=False, default=1)

    is_investing = models.BooleanField(
        verbose_name=_("Investing member"), default=False
    )

    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    signed_membership_agreement = models.BooleanField(
        _("Signed Beteiligungserklärung"), default=False
    )
    paid_membership_fee = models.BooleanField(_("Paid Entrance Fee"), default=False)
    paid_shares = models.BooleanField(_("Paid Shares"), default=False)

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
            and self.first_name
            and self.last_name
            and self.signed_membership_agreement
        )

    def get_info(self):
        """
        get_info is an interface implemented by both ShareOwner and DraftUser
        to allow identical treatment in templates.
        """
        return self


class FinancingCampaign(models.Model):
    is_active = models.BooleanField(_("Currently active"), default=False, null=False)
    name = models.CharField(_("Name"), max_length=150, blank=False, null=False)
    goal = models.IntegerField(_("Goal"), blank=False, null=False)

    def get_absolute_url(self):
        return reverse("coop:financing_campaign_update", args=[self.pk])


class FinancingSource(models.Model):
    name = models.CharField(_("Name"), max_length=150, blank=False, null=False)
    raised_amount = models.IntegerField(
        _("Raised amount"), blank=False, null=False, default=0
    )
    campaign = models.ForeignKey(
        FinancingCampaign,
        related_name="sources",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )


class IncomingPayment(models.Model):
    paying_member = models.ForeignKey(
        ShareOwner,
        verbose_name=_("Paying member"),
        related_name="paying_member",
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )
    credited_member = models.ForeignKey(
        ShareOwner,
        verbose_name=_("Credited member"),
        related_name="credited_member",
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )
    amount = (
        models.PositiveIntegerField(  # TODO Théo 04.06.22 Make this a decimal field
            verbose_name=_("Amount"), null=False, blank=False
        )
    )
    payment_date = models.DateField(
        verbose_name=_("Payment date"), null=False, blank=False
    )
    creation_date = models.DateField(
        verbose_name=_("Creation date"), null=False, blank=False
    )
    comment = models.TextField(blank=True, null=False, default="")
    created_by = models.ForeignKey(
        TapirUser,
        verbose_name=_("Created by"),
        related_name="creator",
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )

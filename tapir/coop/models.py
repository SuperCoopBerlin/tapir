from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tapir.accounts import validators
from tapir.accounts.models import TapirUser
from tapir.finance.models import Invoice
from tapir.odoo.models import OdooPartner
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
        related_name="coop_share_owner",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    is_company = models.BooleanField(verbose_name=_("Is company"), blank=False)
    company_name = models.CharField(max_length=150, blank=True)

    # In the case that this is a company, this is the contact data for the company representative
    # There can also be investing members that do not have a user account
    first_name = models.CharField(_("First name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)

    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")

    is_investing = models.BooleanField(
        verbose_name=_("Is investing member"), default=False
    )

    def clean(self):
        r = super().clean()
        if self.is_company and self.user:
            raise ValidationError(
                _("Cannot be a company share owner and have an associated user")
            )
        return r

    def get_display_name(self):
        if self.user:
            return self.user.get_display_name()
        if self.is_company:
            return self.company_name
        return UserUtils.build_display_name(self.first_name, self.last_name)

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def get_email(self):
        return self.user.email if self.user else self.email

    def get_absolute_url(self):
        if self.user:
            return self.user.get_absolute_url()
        return reverse("coop:shareowner_detail", args=[self.pk])

    def get_oldest_active_share_ownership(self):
        return self.get_active_share_ownerships().order_by("start_date").first()

    def get_active_share_ownerships(self):
        return self.share_ownerships.active_temporal()

    def num_shares(self) -> int:
        return ShareOwnership.objects.filter(owner=self).count()


class ShareOwnership(DurationModelMixin, models.Model):
    """ShareOwnership represents ownership of a single share."""

    owner = models.ForeignKey(
        ShareOwner,
        related_name="share_ownerships",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )


class CoopUser(object):
    def __init__(self, user):
        self.user = user


TapirUser.coop = property(lambda u: CoopUser(u))


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
    phone_number = models.CharField(_("Phone number"), blank=True, max_length=20)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")

    # For now, make this not editable, as one is the 99%-case. In case somebody wants to buy more shares,
    # we should build a flow for existing users. This also solves the issue of keeping the invoice in sync.
    num_shares = models.IntegerField(
        _("Number of Shares"), blank=False, editable=False, default=1
    )
    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    signed_membership_agreement = models.BooleanField(
        _("Signed Beteiligungserklärung"), default=False
    )

    # OdooPartner and Invoice that was already created to process the payment
    odoo_partner = models.ForeignKey(
        OdooPartner, blank=True, null=True, on_delete=models.PROTECT
    )
    coop_share_invoice = models.ForeignKey(
        Invoice, blank=True, null=True, on_delete=models.PROTECT
    )

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

    def create_coop_share_invoice(self):
        # This is a bit hacky, as it's a second codepath that creates an invoice and registers a payment before we even
        # have the User and ShareOwner objects. However, in practice we (mostly) only want to admit people after we've
        # registered their payment, as otherwise we would be running after payments from users that are already
        # admitted.
        if not self.odoo_partner:
            self.odoo_partner = OdooPartner.objects.create_from_draft_user(self)

        if not self.coop_share_invoice:
            self.coop_share_invoice = Invoice.objects.create_with_odoo_partner(
                self.odoo_partner
            )
            self.coop_share_invoice.add_invoice_line(
                "Eintrittsgeld",
                COOP_ENTRY_AMOUNT,
                settings.ODOO_ACCOUNT_ID_8200,
                settings.ODOO_TAX_ID_NOT_TAXABLE,
            )
            self.coop_share_invoice.add_invoice_line(
                "Genossenschaftsanteil",
                COOP_SHARE_PRICE,
                settings.ODOO_ACCOUNT_ID_0810,
                settings.ODOO_TAX_ID_NOT_TAXABLE,
            )
            self.coop_share_invoice.mark_open()

        self.save()

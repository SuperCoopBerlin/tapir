from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tapir.accounts import validators
from tapir.accounts.models import TapirUser
from tapir.utils.models import DurationModelMixin


COOP_SHARE_PRICE = Decimal(100)
COOP_ENTRY_COST = Decimal(10)


class ShareOwner(models.Model):
    """ShareOwner represents an owner of a ShareOwnership.

    Usually, this is just a proxy for the associated user. However, it may also be used to
    represent a person or company that does not have their own account.
    """

    user = models.OneToOneField(
        TapirUser,
        related_name="coop_share_owner",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    is_company = models.BooleanField(verbose_name=_("Is company"))
    company_name = models.CharField(max_length=150, blank=True)

    # In the case that this is a company, this is the contact data for the company representative
    first_name = models.CharField(_("First name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)

    def clean(self):
        r = super().clean()
        if self.is_company and self.user:
            raise ValidationError(
                _("Cannot be a company share owner and have an associated user")
            )
        return r

    def get_display_name(self):
        if self.user:
            return self.user.get_full_name()
        if self.is_company:
            return "%s: %s (%s %s)" % (
                _("Company"),
                self.company_name,
                self.first_name,
                self.last_name,
            )
        return "%s %s" % (self.first_name, self.last_name)

    def get_absolute_url(self):
        if self.user:
            return self.user.get_absolute_url()
        return super().get_absolute_url()


class ShareOwnership(DurationModelMixin, models.Model):
    """ShareOwnership represents ownership of a single share."""

    user = models.ForeignKey(
        ShareOwner,
        related_name="share_ownerships",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    is_investing = models.BooleanField(
        verbose_name=_("Is investing member"), default=False
    )


class CoopUser(object):
    def __init__(self, user):
        self.user = user


TapirUser.coop = property(lambda u: CoopUser(u))


class DraftUser(models.Model):
    username_validator = validators.UsernameValidator

    username = models.CharField(
        _("username"), max_length=150, validators=[username_validator],
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)

    num_shares = models.IntegerField(_("Number of Shares"), blank=False, default=1)
    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    signed_membership_agreement = models.BooleanField(
        _("Signed Beteiligungserklärung"), default=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("coop:draftuser_detail", args=[self.pk,],)

    def get_initial_amount(self):
        return self.num_shares * COOP_SHARE_PRICE + COOP_ENTRY_COST

    def get_display_name(self):
        if self.first_name or self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        if self.email:
            return self.email

        return self.username

    def can_create_user(self):
        return (
            self.email
            and self.username
            and self.first_name
            and self.last_name
            and self.signed_membership_agreement
        )

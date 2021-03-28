from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tapir.accounts import validators
from tapir.accounts.models import TapirUser
from tapir.utils.models import DurationModelMixin


class CoopShareOwnership(DurationModelMixin, models.Model):
    """CoopShareOwnership represents ownership of a single share."""

    user = models.ForeignKey(
        TapirUser,
        related_name="coop_share_ownerships",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )


class CoopUser(object):
    def __init__(self, user):
        self.user = user

    def is_coop_member(self):
        return CoopShareOwnership.objects.active_temporal().exists()


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

    def get_display_name(self):
        if self.first_name or self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        if self.email:
            return self.email

        return self.username

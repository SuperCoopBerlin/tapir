from django.db import models

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


TapirUser.shifts = property(lambda u: ShiftUser(u))

import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderActiveMembersWithAccount(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Active members with Tapir account")

    @classmethod
    def get_description(cls):
        return _(
            "Same as active members, but also had an account at the given date. Some members declare themselves active when joining the coop but never come to activate their account."
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()
        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_date
        ).distinct()
        active_members_with_account = TapirUser.objects.filter(
            share_owner__in=active_members, date_joined__lte=reference_date
        )
        return ShareOwner.objects.filter(user__in=active_members_with_account)

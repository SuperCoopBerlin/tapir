import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderActiveMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Active members")

    @classmethod
    def get_description(cls):
        return _(
            "Active in the sense of their membership: paused and investing members are not active, but frozen members are active"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()
        return ShareOwner.objects.with_status(MemberStatus.ACTIVE, reference_date)

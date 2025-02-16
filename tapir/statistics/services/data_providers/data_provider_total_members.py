import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderTotalMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Total members")

    @classmethod
    def get_description(cls):
        return _("Ignoring status: investing and paused members are included")

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()
        share_owner_ids = set()
        for member_status in [
            MemberStatus.ACTIVE,
            MemberStatus.PAUSED,
            MemberStatus.INVESTING,
        ]:
            share_owner_ids.update(
                ShareOwner.objects.with_status(member_status, reference_date)
                .distinct()
                .values_list("id", flat=True)
            )
        return ShareOwner.objects.filter(id__in=share_owner_ids)

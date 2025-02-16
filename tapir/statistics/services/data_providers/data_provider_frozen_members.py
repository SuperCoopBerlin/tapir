import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderFrozenMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Frozen members")

    @classmethod
    def get_description(cls):
        return _(
            "Counted out of 'active' members: paused and investing members not counted."
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        share_owners = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_time
        )

        share_owners = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            share_owners, reference_time
        )

        return share_owners.filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: True}
        )

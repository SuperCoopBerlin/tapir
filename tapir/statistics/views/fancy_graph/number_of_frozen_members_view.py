import datetime

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfFrozenMembersAtDateView(DatapointView):
    permission_required = PERMISSION_COOP_MANAGE

    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        return self.get_members_frozen_at_datetime(reference_time)

    @staticmethod
    def get_members_frozen_at_datetime(reference_time):
        share_owners = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_time
        )

        share_owners = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            share_owners, reference_time
        )

        return share_owners.filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: True}
        )

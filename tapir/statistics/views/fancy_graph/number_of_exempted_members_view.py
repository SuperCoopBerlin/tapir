import datetime

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.models import ShiftExemption
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfExemptedMembersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        reference_date = reference_time.date()
        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_date
        )

        active_members = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            active_members, reference_time
        )

        not_frozen_members = active_members.filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: False}
        )

        members_that_joined_before_date = not_frozen_members.filter(
            user__date_joined__lte=reference_time
        )

        exemptions = ShiftExemption.objects.active_temporal(reference_date)
        exemptions.filter(
            shift_user_data__user__share_owner__in=members_that_joined_before_date
        )

        return exemptions.filter(
            shift_user_data__user__share_owner__in=members_that_joined_before_date
        ).count()

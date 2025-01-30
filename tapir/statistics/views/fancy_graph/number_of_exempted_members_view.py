import datetime

from django.db.models import Q, QuerySet

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.models import ShiftExemption
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfExemptedMembersAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_time
        )
        active_members_ids = list(active_members.values_list("id", flat=True))

        members_not_frozen = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            ShareOwner.objects.all(), reference_time
        ).filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: False}
        )
        members_not_frozen_ids = list(members_not_frozen.values_list("id", flat=True))

        members_that_joined_before_date = ShareOwner.objects.filter(
            user__date_joined__lte=reference_time
        )
        members_that_joined_before_date_ids = list(
            members_that_joined_before_date.values_list("id", flat=True)
        )

        exemptions = ShiftExemption.objects.active_temporal(reference_date)
        members_exempted = ShareOwner.objects.filter(
            user__shift_user_data__shift_exemptions__in=exemptions
        ).distinct()
        members_exempted_ids = list(members_exempted.values_list("id", flat=True))

        all_criteria = Q()
        for id_list in [
            active_members_ids,
            members_not_frozen_ids,
            members_that_joined_before_date_ids,
            members_exempted_ids,
        ]:
            all_criteria &= Q(id__in=id_list)

        return ShareOwner.objects.filter(all_criteria)

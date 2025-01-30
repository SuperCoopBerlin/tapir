import datetime

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfWorkingMembersAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        queryset = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), reference_time
        )

        queryset = queryset.filter(
            **{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True}
        )

        return ShareOwner.objects.filter(user__shift_user_data__in=queryset)

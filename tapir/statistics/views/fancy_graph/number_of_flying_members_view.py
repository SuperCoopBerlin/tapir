import datetime

from django.db.models import Q

from tapir.shifts.models import ShiftAttendanceMode, ShiftUserData
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.views.fancy_graph.base_view import (
    DatapointView,
)


class NumberOfFlyingMembersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        shift_user_datas = ShiftUserData.objects.all()

        shift_user_datas_working = (
            ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
                shift_user_datas, reference_time
            )
        ).filter(**{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True})
        shift_user_datas_working_ids = list(
            shift_user_datas_working.values_list("id", flat=True)
        )

        shift_user_datas_flying = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_time
        ).filter(
            **{
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.FLYING
            }
        )
        shift_user_datas_flying_ids = list(
            shift_user_datas_flying.values_list("id", flat=True)
        )

        return (
            ShiftUserData.objects.filter(
                Q(id__in=shift_user_datas_working_ids)
                & Q(id__in=shift_user_datas_flying_ids)
            )
            .distinct()
            .count()
        )

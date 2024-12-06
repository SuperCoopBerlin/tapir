import datetime

from tapir.shifts.models import ShiftAttendanceMode
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.statistics.views.fancy_graph.base_view import (
    DatapointView,
    get_shift_user_datas_of_working_members_annotated_with_attendance_mode,
)


class NumberOfFlyingMembersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        shift_user_datas = (
            get_shift_user_datas_of_working_members_annotated_with_attendance_mode(
                reference_time
            )
        )

        shift_user_datas = shift_user_datas.filter(
            **{
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.FLYING
            }
        )

        return shift_user_datas.count()

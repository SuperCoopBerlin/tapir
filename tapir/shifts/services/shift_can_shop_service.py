import datetime

from tapir.shifts.models import ShiftUserData, ShiftAttendanceMode
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)


class ShiftCanShopService:
    @classmethod
    def can_shop(cls, shift_user_data: ShiftUserData, at_date: datetime.date = None):
        return (
            ShiftAttendanceModeService.get_attendance_mode(shift_user_data, at_date)
            != ShiftAttendanceMode.FROZEN
        )

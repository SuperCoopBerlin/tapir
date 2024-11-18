from __future__ import annotations

import datetime
import typing

from tapir.shifts.models import ShiftAttendanceMode, ShiftUserData
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)

if typing.TYPE_CHECKING:
    from tapir.coop.models import ShareOwner


class ShiftCanShopService:
    @classmethod
    def can_shop(
        cls, member_object: ShiftUserData | ShareOwner, at_date: datetime.date = None
    ):
        return (
            ShiftAttendanceModeService.get_attendance_mode(member_object, at_date)
            != ShiftAttendanceMode.FROZEN
        )

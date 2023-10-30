import datetime

from tapir.accounts.models import TapirUser
from tapir.coop.models import MembershipPause
from tapir.shifts.models import ShiftAttendanceTemplate, ShiftAttendance
from tapir.utils.shortcuts import get_timezone_aware_datetime


class MembershipPauseService:
    @staticmethod
    def on_pause_created_or_updated(pause: MembershipPause):
        tapir_user: TapirUser = getattr(pause.share_owner, "user", None)
        if not tapir_user:
            return

        pause_start_as_datetime = get_timezone_aware_datetime(
            pause.start_date, datetime.time()
        )
        pause_end_as_datetime = get_timezone_aware_datetime(
            pause.start_date, datetime.time(hour=23, minute=59)
        )

        for attendance_template in ShiftAttendanceTemplate.objects.filter(
            user=tapir_user
        ):
            attendance_template.cancel_attendances(pause_start_as_datetime)
            attendance_template.delete()

        for attendance in ShiftAttendance.objects.filter(
            user=tapir_user,
            slot__shift__start_time__gte=pause_start_as_datetime,
            slot__shift__end_time__lte=pause_end_as_datetime,
            state=ShiftAttendance.State.PENDING,
        ):
            attendance.state = ShiftAttendance.State.CANCELLED
            attendance.save()

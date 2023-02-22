from django.db import transaction
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.log.util import freeze_for_log
from tapir.shifts.emails.member_frozen_email import MemberFrozenEmail
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceTemplate,
    ShiftAttendance,
)


class FrozenStatusService:
    FREEZE_THRESHOLD = -5

    def should_freeze_member(
        self, shift_user_data: ShiftUserData, last_balance_change: int
    ):
        # Do this check after applying an account balance change
        return (
            last_balance_change < 0
            and shift_user_data.attendance_mode is not ShiftAttendanceMode.FROZEN
            and shift_user_data.get_account_balance() <= self.FREEZE_THRESHOLD
        )

    def freeze_member(self, shift_user_data: ShiftUserData, actor: TapirUser | None):
        with transaction.atomic():
            self._update_attendance_mode_and_create_log_entry(shift_user_data, actor)
            self._cancel_future_attendances(shift_user_data)
            ShiftAttendanceTemplate.objects.filter(user=shift_user_data.user).delete()
            email = MemberFrozenEmail()
        email.send_to_tapir_user(actor=actor, recipient=shift_user_data.user)

    @staticmethod
    def _update_attendance_mode_and_create_log_entry(
        shift_user_data: ShiftUserData, actor: TapirUser | None
    ):
        old_data = freeze_for_log(shift_user_data)
        shift_user_data.attendance_mode = ShiftAttendanceMode
        new_data = freeze_for_log(shift_user_data)
        if old_data != new_data:
            UpdateShiftUserDataLogEntry().populate(
                old_frozen=old_data,
                new_frozen=new_data,
                tapir_user=shift_user_data.user,
                actor=actor,
            ).save()

    @staticmethod
    def _cancel_future_attendances(shift_user_data: ShiftUserData):
        attendances = ShiftAttendance.objects.filter(
            user=shift_user_data.user,
            slot__shift__start_time__gte=timezone.now(),
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
        )
        for attendance in attendances:
            attendance.state = ShiftAttendance.State.CANCELLED
            attendance.excused_reason = f"Shift mode set to frozen at {timezone.now().strftime('%Y-%m-%dT%H:%M')}"
            attendance.save()

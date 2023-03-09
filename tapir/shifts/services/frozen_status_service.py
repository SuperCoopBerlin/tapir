import datetime

from django.db import transaction
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.log.util import freeze_for_log
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceTemplate,
    ShiftAccountEntry,
    ShiftAttendance,
)


class FrozenStatusService:
    FREEZE_THRESHOLD = -4
    FREEZE_AFTER_DAYS = 10

    @classmethod
    def should_freeze_member(cls, shift_user_data: ShiftUserData) -> bool:
        if shift_user_data.attendance_mode is ShiftAttendanceMode.FROZEN:
            return False

        if not cls._is_member_below_threshold_since_long_enough(shift_user_data):
            return False

        if cls._is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
            shift_user_data
        ):
            return False

        return True

    @classmethod
    def _is_member_below_threshold_since_long_enough(
        cls, shift_user_data: ShiftUserData
    ) -> bool:
        balance = shift_user_data.get_account_balance()
        if balance > cls.FREEZE_THRESHOLD:
            return False

        entries = ShiftAccountEntry.objects.filter(user=shift_user_data.user).order_by(
            "-date"
        )
        for entry in entries:
            if (timezone.now().date() - entry.date).days > cls.FREEZE_AFTER_DAYS:
                return True
            balance -= entry.value
            if balance > cls.FREEZE_THRESHOLD:
                return False

    @classmethod
    def _is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
        cls, shift_user_data: ShiftUserData
    ) -> bool:
        upcoming_shifts = ShiftAttendance.objects.filter(
            user=shift_user_data.user,
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
            slot__shift__start_time__gt=timezone.now(),
            slot__shift__start_time__lt=timezone.now() + datetime.timedelta(weeks=8),
        )
        return upcoming_shifts.count() >= -shift_user_data.get_account_balance()

    @classmethod
    def freeze_member_and_send_email(
        cls, shift_user_data: ShiftUserData, actor: TapirUser | None
    ):
        with transaction.atomic():
            cls._update_attendance_mode_and_create_log_entry(shift_user_data, actor)
            cls._cancel_future_attendances_templates(shift_user_data)
            ShiftAttendanceTemplate.objects.filter(user=shift_user_data.user).delete()
        from tapir.shifts.emails.member_frozen_email import MemberFrozenEmail

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
    def _cancel_future_attendances_templates(shift_user_data: ShiftUserData):
        for attendance_template in ShiftAttendanceTemplate.objects.filter(
            user=shift_user_data.user
        ):
            attendance_template.cancel_attendances(timezone.now())
            attendance_template.delete()

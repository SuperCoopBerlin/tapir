from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
    Shift,
)


class SelfUnregisterService:
    @classmethod
    def should_show_is_abcd_attendance_reason(
        cls, user: TapirUser, attendance: ShiftAttendance
    ):
        if not attendance.slot.slot_template:
            return False

        return ShiftAttendanceTemplate.objects.filter(
            user=user, slot_template=attendance.slot.slot_template
        ).exists()

    @classmethod
    def should_show_not_enough_days_before_shift_reason(
        cls, attendance: ShiftAttendance, **_
    ):
        return (
            attendance.slot.shift.start_time.date() - timezone.now().date()
        ).days <= Shift.NB_DAYS_FOR_SELF_UNREGISTER

    @classmethod
    def build_reasons_why_cant_self_unregister(
        cls, user: TapirUser, attendance: ShiftAttendance
    ):
        return [
            message
            for check, message in cls.get_check_to_message_map().items()
            if check(
                user=user,
                attendance=attendance,
            )
        ]

    @classmethod
    def user_can_self_unregister(
        cls, user: TapirUser, attendance: ShiftAttendance
    ) -> bool:
        for check in cls.get_check_to_message_map().keys():
            if check(user=user, attendance=attendance):
                return False

        return True

    @classmethod
    def get_check_to_message_map(cls):
        return {
            cls.should_show_is_abcd_attendance_reason: _(
                "It is not possible to unregister from a shift that comes from your ABCD shift."
            ),
            cls.should_show_not_enough_days_before_shift_reason: _(
                "It is only possible to unregister from a shift at least 7 days before the shift."
            ),
        }

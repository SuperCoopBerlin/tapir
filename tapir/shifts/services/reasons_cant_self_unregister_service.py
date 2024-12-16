from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.shifts.models import ShiftAttendance, ShiftAttendanceTemplate, Shift


class ReasonsCantSelfUnregisterService:
    @staticmethod
    def should_show_is_abcd_attendance_reason(
        user: TapirUser, attendance: ShiftAttendance
    ):
        if not attendance.slot.slot_template:
            return False

        return ShiftAttendanceTemplate.objects.filter(
            user=user, slot_template=attendance.slot.slot_template
        ).exists()

    @staticmethod
    def should_show_not_enough_days_before_shift_reason(attendance: ShiftAttendance):
        return (
            attendance.slot.shift.start_time.date() - timezone.now().date()
        ).days <= Shift.NB_DAYS_FOR_SELF_UNREGISTER

    @classmethod
    def build_reasons_why_cant_self_unregister(
        cls, user: TapirUser, attendance: ShiftAttendance
    ):
        reasons_why_cant_self_unregister = []

        if cls.should_show_not_enough_days_before_shift_reason(attendance):
            reasons_why_cant_self_unregister.append(
                _(
                    "It is only possible to unregister from a shift at least 7 days before the shift."
                )
            )

        if cls.should_show_is_abcd_attendance_reason(user, attendance):
            reasons_why_cant_self_unregister.append(
                _(
                    "It is not possible to unregister from a shift that comes from your ABCD shift."
                )
            )

        return reasons_why_cant_self_unregister

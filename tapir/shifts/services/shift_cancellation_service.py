from django.db import transaction

from tapir.shifts.models import Shift, ShiftAttendance


class ShiftCancellationService:
    """Logic for cancelling shifts handles logic for setting attendance of
    shift attendees"""

    @staticmethod
    def cancel(shift: Shift):
        with transaction.atomic():
            shift.cancelled = True
            shift.save()

            for slot in shift.slots.all():
                attendance = slot.get_valid_attendance()
                if not attendance:
                    continue
                if (
                    hasattr(slot.slot_template, "attendance_template")
                    and slot.slot_template.attendance_template.user == attendance.user
                ):
                    attendance.state = ShiftAttendance.State.MISSED_EXCUSED
                    attendance.excused_reason = "Shift cancelled"
                    attendance.save()
                    attendance.update_shift_account_entry()
                else:
                    attendance.state = ShiftAttendance.State.CANCELLED
                    attendance.save()

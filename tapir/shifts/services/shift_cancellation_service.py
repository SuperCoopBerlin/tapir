from django.db import transaction

from tapir.shifts.models import Shift, ShiftAttendance


class ShiftCancellationService:
    """Service for handling canceling a shift and updating attendances for the registered users."""

    @staticmethod
    def cancel(shift: Shift):
        """Cancels the given shift and updates attendances accordingly.

        If the attendance is for an ABCD shift (i.e. has an attendance template
        linked to the slot template), the attendance is marked as MISSED_EXCUSED.
        Otherwise, it is marked as CANCELLED.

        Note that the cancellation reason must be set by the caller on the shift
        object before calling this method. This method saves the modified shift
        object.

        Args:
            shift (Shift): The shift to cancel.
        """
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

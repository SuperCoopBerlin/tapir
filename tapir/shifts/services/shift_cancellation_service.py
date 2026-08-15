from django.contrib.auth.models import User
from django.db import transaction

from tapir.accounts.models import TapirUser
from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_cancelled_mail import ShiftCancelledEmail
from tapir.shifts.models import Shift, ShiftAttendance


class ShiftCancellationService:
    """Service for handling canceling a shift and updating attendances for the registered users."""

    @staticmethod
    @transaction.atomic
    def cancel(
        shift: Shift,
        actor: TapirUser | User | None = None,
        grant_shift_credits: bool = True,
    ):
        """Cancels the given shift and updates attendances accordingly.

        If the attendance is for an ABCD shift (i.e. has an attendance template
        linked to the slot template), the attendance is marked as MISSED_EXCUSED
        (if grant_shift_credits is True) or CANCELLED (if grant_shift_credits is False).
        Otherwise, it is marked as CANCELLED.

        Note that the cancellation reason must be set by the caller on the shift
        object before calling this method. This method saves the modified shift
        object.

        Args:
            shift (Shift): The shift to cancel.
            actor
        """
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
                attendance.state = (
                    ShiftAttendance.State.MISSED_EXCUSED
                    if grant_shift_credits
                    else ShiftAttendance.State.CANCELLED
                )
                attendance.excused_reason = "Shift cancelled"
                attendance.save()
                attendance.update_shift_account_entry()
                user_is_registered_to_an_abcd_shift = True

            else:
                attendance.state = ShiftAttendance.State.CANCELLED
                attendance.save()
                user_is_registered_to_an_abcd_shift = False

            email_builder = ShiftCancelledEmail(
                shift=shift,
                user_is_registered_to_an_abcd_shift=user_is_registered_to_an_abcd_shift,
            )
            SendMailService.send_to_tapir_user(
                actor=actor,
                recipient=attendance.user,
                email_builder=email_builder,
            )

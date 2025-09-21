import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.models import (
    ShiftWatch,
    StaffingStatusChoices,
    ShiftUserCapability,
    ShiftSlot,
    ShiftAttendance,
)


def get_staffing_status(
    number_of_available_slots: int,
    valid_attendances: int,
    required_attendances: int,
    last_status: str = None,
):
    """Determine the staffing status based on attendance counts."""
    if (
        valid_attendances < required_attendances
        and last_status != StaffingStatusChoices.UNDERSTAFFED
    ):
        return StaffingStatusChoices.UNDERSTAFFED
    elif (
        number_of_available_slots - valid_attendances == 1
        and last_status != StaffingStatusChoices.ALMOST_FULL
    ):
        return StaffingStatusChoices.ALMOST_FULL
    elif (
        number_of_available_slots - valid_attendances == 0
        and last_status != StaffingStatusChoices.FULL
    ):
        return StaffingStatusChoices.FULL
    elif (
        valid_attendances >= required_attendances
        and last_status == StaffingStatusChoices.UNDERSTAFFED
    ):
        # When it's ok now but last status was understaffed
        return StaffingStatusChoices.ALL_CLEAR
    return None


def get_shift_coordinator_status(
    this_valid_slot_ids: list[int], last_valid_slot_ids: list[int]
):
    # Team-leader/Shift-Coordinator notifications
    def is_shift_coordinator_available(slot_ids: list[int]):
        return ShiftSlot.objects.filter(
            id__in=slot_ids,
            required_capabilities__contains=[ShiftUserCapability.SHIFT_COORDINATOR],
        )

    this_sc_available = is_shift_coordinator_available(this_valid_slot_ids)
    last_sc_available = is_shift_coordinator_available(last_valid_slot_ids)
    if not this_sc_available and last_sc_available:
        return StaffingStatusChoices.SHIFT_COORDINATOR_MINUS
    elif this_sc_available and not last_sc_available:
        return StaffingStatusChoices.SHIFT_COORDINATOR_PLUS
    return None


class Command(BaseCommand):
    help = "Sent to a member when there is a relevant change in shift staffing and the member wants to know about it."

    def handle(self, *args, **options):
        for shift_watch_data in ShiftWatch.objects.filter(
            shift__start_time__gte=timezone.now()
        ).select_related("user", "shift"):
            self.send_shift_watch_mail_per_user_and_shift(shift_watch_data)

    def send_shift_watch_mail_per_user_and_shift(self, shift_watch_data: ShiftWatch):
        notification_reasons: list[StaffingStatusChoices] = []

        this_valid_slot_ids = list(
            ShiftSlot.objects.filter(
                shift=shift_watch_data.shift,
                attendances__state=ShiftAttendance.State.PENDING,
            ).values_list("id", flat=True)
        )

        valid_attendances_count = len(this_valid_slot_ids)
        required_attendances_count = (
            shift_watch_data.shift.get_num_required_attendances()
        )
        number_of_available_slots = shift_watch_data.shift.slots.count()

        # Determine staffing status
        current_status = get_staffing_status(
            number_of_available_slots=number_of_available_slots,
            valid_attendances=valid_attendances_count,
            required_attendances=required_attendances_count,
            last_status=shift_watch_data.last_staffing_status,
        )
        if current_status:
            notification_reasons.append(current_status)
            shift_watch_data.last_staffing_status = current_status

        # Check shift coordinator status
        shift_coordinator_status = get_shift_coordinator_status(
            this_valid_slot_ids, shift_watch_data.last_valid_slot_ids
        )
        if shift_coordinator_status is not None:
            notification_reasons.append(shift_coordinator_status)

        # General attendance change notifications
        if not notification_reasons:
            # If no other status like "Understaffed" or "teamleader registered" appeared, inform user about general change
            if valid_attendances_count > len(shift_watch_data.last_valid_slot_ids):
                notification_reasons.append(StaffingStatusChoices.ATTENDANCE_PLUS)
            elif valid_attendances_count < len(shift_watch_data.last_valid_slot_ids):
                notification_reasons.append(StaffingStatusChoices.ATTENDANCE_MINUS)

        # Send notifications
        for reason in notification_reasons:
            if reason.value in shift_watch_data.staffing_status:
                self.send_shift_watch_mail(
                    shift_watch=shift_watch_data, staffing_status=reason
                )

        shift_watch_data.last_valid_slot_ids = this_valid_slot_ids
        shift_watch_data.save()

    @staticmethod
    def send_shift_watch_mail(
        shift_watch: ShiftWatch, staffing_status: StaffingStatusChoices
    ):
        email_builder = ShiftWatchEmailBuilder(
            shift_watch=shift_watch,
            staffing_status=staffing_status,
        )
        SendMailService.send_to_tapir_user(
            actor=None,
            recipient=shift_watch.user,
            email_builder=email_builder,
        )
        time.sleep(0.1)

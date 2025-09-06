import time

from django.core.management.base import BaseCommand

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.models import (
    ShiftWatch,
    StaffingEventsChoices,
    ShiftUserCapability,
    ShiftSlot,
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
        and last_status != StaffingEventsChoices.UNDERSTAFFED
    ):
        return StaffingEventsChoices.UNDERSTAFFED
    elif (
        number_of_available_slots - valid_attendances == 1
        and last_status != StaffingEventsChoices.ALMOST_FULL
    ):
        return StaffingEventsChoices.ALMOST_FULL
    elif (
        number_of_available_slots - valid_attendances == 0
        and last_status != StaffingEventsChoices.FULL
    ):
        return StaffingEventsChoices.FULL
    elif last_status == StaffingEventsChoices.UNDERSTAFFED:
        # When it's ok now but last status was understaffed
        return StaffingEventsChoices.ALL_CLEAR
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
        return StaffingEventsChoices.SHIFT_COORDINATOR_MINUS
    elif this_sc_available and not last_sc_available:
        return StaffingEventsChoices.SHIFT_COORDINATOR_PLUS
    return None


class Command(BaseCommand):
    help = "Sent to a member when there is a relevant change in shift staffing and the member wants to know about it."

    def handle(self, *args, **options):
        for shift_watch_data in ShiftWatch.objects.select_related("user", "shift"):
            notification_reasons = []
            this_valid_slot_ids = [
                s.slot_id for s in shift_watch_data.shift.get_valid_attendances()
            ]
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
                last_status=get_staffing_status(
                    number_of_available_slots=number_of_available_slots,
                    valid_attendances=len(shift_watch_data.last_valid_slot_ids),
                    required_attendances=required_attendances_count,
                ),
            )
            if current_status:
                notification_reasons.append(current_status)

            # Check shift coordinator status
            if (
                result := get_shift_coordinator_status(
                    this_valid_slot_ids, shift_watch_data.last_valid_slot_ids
                )
            ) is not None:
                notification_reasons.append(result)

            # General attendance change notifications
            if not notification_reasons:
                # If no other status like "Understaffed" or "teamleader registered" appeared, inform user about general change
                if shift_watch_data.shift.get_valid_attendances().count() > len(
                    shift_watch_data.last_valid_slot_ids
                ):
                    notification_reasons.append(StaffingEventsChoices.ATTENDANCE_PLUS)
                elif shift_watch_data.shift.get_valid_attendances().count() < len(
                    shift_watch_data.last_valid_slot_ids
                ):
                    notification_reasons.append(StaffingEventsChoices.ATTENDANCE_MINUS)

            # Send notifications
            for reason in notification_reasons:
                if reason.value in shift_watch_data.staffing_events:
                    self.send_shift_watch_mail(
                        shift_watch=shift_watch_data, reason=reason.label
                    )

            shift_watch_data.last_valid_slot_ids = this_valid_slot_ids
            shift_watch_data.save()

    @staticmethod
    def send_shift_watch_mail(shift_watch: ShiftWatch, reason: str):
        email_builder = ShiftWatchEmailBuilder(
            shift=shift_watch.shift,
            reason=f"{reason}: {shift_watch.shift.get_display_name()}",
        )
        SendMailService.send_to_tapir_user(
            actor=None,
            recipient=shift_watch.user,
            email_builder=email_builder,
        )
        time.sleep(0.1)

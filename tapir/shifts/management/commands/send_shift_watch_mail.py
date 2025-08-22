import time

from IPython.utils.wildcard import is_type
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.models import (
    ShiftWatch,
    StaffingEventsChoices,
    Shift,
    ShiftUserCapability,
    ShiftSlot,
)


def get_staffing_status(
    shift: Shift, last_status: str, last_number_of_attendances: int
):
    if shift.get_valid_attendances().count() < shift.get_num_required_attendances():
        return StaffingEventsChoices.UNDERSTAFFED
    elif shift.slots.count() - shift.get_valid_attendances().count() == 1:
        return StaffingEventsChoices.ALMOST_FULL
    elif shift.slots.count() - shift.get_valid_attendances().count() == 0:
        return StaffingEventsChoices.FULL
    elif last_status == StaffingEventsChoices.UNDERSTAFFED:
        return StaffingEventsChoices.ALL_CLEAR
    elif shift.get_valid_attendances().count() > last_number_of_attendances:
        return StaffingEventsChoices.ATTENDANCE_PLUS
    elif shift.get_valid_attendances().count() < last_number_of_attendances:
        return StaffingEventsChoices.ATTENDANCE_MINUS
    else:
        return None


def is_shift_coordinator_available(slot_ids: list[int]):
    return ShiftSlot.objects.filter(
        Q(id__in=slot_ids)
        & Q(required_capabilities__contains=[ShiftUserCapability.SHIFT_COORDINATOR])
    ).exists()


class Command(BaseCommand):
    help = "Sent to a member when there is a relevant change in shift staffing and the member wants to know about it."

    def handle(self, *args, **options):
        for shift_watch_data in ShiftWatch.objects.select_related("user", "shift"):

            notification_reasons = []
            current_status = get_staffing_status(
                shift=shift_watch_data.shift,
                last_status=shift_watch_data.last_reason_for_notification,
                last_number_of_attendances=len(shift_watch_data.last_valid_slot_ids),
            )
            if (shift_watch_data.last_reason_for_notification != current_status) and (
                current_status is not None
            ):
                notification_reasons.append(current_status)

            # Team-leader/Shift-Coordinator checking
            this_valid_slot_ids = [
                s.slot_id for s in shift_watch_data.shift.get_valid_attendances()
            ]
            this_sc_available = is_shift_coordinator_available(this_valid_slot_ids)
            last_sc_available = is_shift_coordinator_available(
                shift_watch_data.last_valid_slot_ids
            )
            if not this_sc_available and last_sc_available:
                notification_reasons.append(
                    StaffingEventsChoices.SHIFT_COORDINATOR_MINUS
                )
            elif this_sc_available and not last_sc_available:
                notification_reasons.append(
                    StaffingEventsChoices.SHIFT_COORDINATOR_PLUS
                )

            for reason in shift_watch_data.staffing_events:
                if reason in shift_watch_data.staffing_events:
                    self.send_shift_watch_mail(
                        shift_watch=shift_watch_data, reason=reason
                    )

            with transaction.atomic():
                shift_watch_data.last_reason_for_notification = current_status
                shift_watch_data.last_valid_slot_ids = this_valid_slot_ids
                shift_watch_data.save()

    @staticmethod
    def send_shift_watch_mail(shift_watch: ShiftWatch, reason: str):
        with transaction.atomic():
            email_builder = ShiftWatchEmailBuilder(
                shift=shift_watch.shift,
                reason=f"{reason}: {shift_watch.shift.get_display_name()}",
            )
            SendMailService.send_to_tapir_user(
                actor=None,
                recipient=shift_watch.user,
                email_builder=email_builder,
            )
            shift_watch.save()
        time.sleep(0.1)

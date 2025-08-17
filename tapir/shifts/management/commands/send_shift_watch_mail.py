import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, QuerySet
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.models import ShiftWatch, StaffingEventsChoices, Shift


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


class Command(BaseCommand):
    help = "Sent to a member when there is a relevant change in shift staffing and the member wants to know about it."

    def handle(self, *args, **options):
        for shift_watch_data in ShiftWatch.objects.select_related("user", "shift"):
            current_status = get_staffing_status(
                shift=shift_watch_data.shift,
                last_status=shift_watch_data.last_reason_for_notification,
                last_number_of_attendances=shift_watch_data.last_number_of_attendances,
            )
            if (shift_watch_data.last_reason_for_notification != current_status) and (
                current_status is not None
            ):
                if current_status in shift_watch_data.staffing_events:
                    self.send_shift_watch_mail(shift_watch_data, reason=current_status)

                with transaction.atomic():
                    shift_watch_data.last_reason_for_notification = current_status
                    shift_watch_data.last_number_of_attendances = (
                        shift_watch_data.shift.get_valid_attendances().count()
                    )
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

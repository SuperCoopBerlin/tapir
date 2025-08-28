import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.management.commands.send_shift_watch_mail import get_staffing_events
from tapir.shifts.models import ShiftWatch, StaffingEventsChoices


class Command(BaseCommand):
    help = "Sent as reminder to a member that a shift is still understaffed."

    def handle(self, *args, **options):
        tomorrow = timezone.now().date() + timedelta(days=1)
        shifts_tomorrow = ShiftWatch.objects.filter(shift__end_time__date=tomorrow)

        for shift_watch_data in shifts_tomorrow:
            current_status = get_staffing_events(
                shift=shift_watch_data.shift,
                last_status=shift_watch_data.last_reason_for_notification,
                last_number_of_attendances=len(shift_watch_data.last_valid_slot_ids),
            )
            if current_status == StaffingEventsChoices.UNDERSTAFFED:
                self.send_shift_watch_mail(shift_watch_data, reason=current_status)

    @staticmethod
    def send_shift_watch_mail(shift_watch: ShiftWatch, reason: str):
        with transaction.atomic():
            email_builder = ShiftWatchEmailBuilder(
                shift=shift_watch.shift,
                reason=f"Reminder {reason}: {shift_watch.shift.get_display_name()}",
            )
            SendMailService.send_to_tapir_user(
                actor=None,
                recipient=shift_watch.user,
                email_builder=email_builder,
            )
            shift_watch.save()
        time.sleep(0.1)

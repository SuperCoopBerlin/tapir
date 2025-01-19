import datetime
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts import config
from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmailBuilder
from tapir.shifts.emails.shift_understaffed_watch_mail import (
    ShiftUnderstaffedEmailBuilder,
)
from tapir.shifts.models import ShiftUserData, ShiftAttendance, ShiftWatch


class Command(BaseCommand):
    help = "Sends  emails to every member that a certain shift is understaffed"

    def handle(self, *args, **options):
        for shift_watch_data in ShiftWatch.objects.filter(
            shift__start_time__gte=timezone.now(),
            shift__start_time__lte=timezone.now()
            + datetime.timedelta(days=config.REMINDER_EMAIL_DAYS_BEFORE_SHIFT),
        ):
            self.send_shift_understaffed_mail(shift_watch_data)

    @staticmethod
    def send_shift_understaffed_mail(shift_watch: ShiftWatch):
        for shift_watches in shift_watch.objects.select_related(
            "user", "shift_watched"
        ):
            with transaction.atomic():
                email_builder = ShiftUnderstaffedEmailBuilder(
                    shift=shift_watches.shift_watched
                )
                SendMailService.send_to_tapir_user(
                    actor=None,
                    recipient=shift_watches.user,
                    email_builder=email_builder,
                )
            time.sleep(0.1)

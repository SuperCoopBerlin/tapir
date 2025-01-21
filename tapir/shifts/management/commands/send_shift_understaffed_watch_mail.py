import time

from django.core.management.base import BaseCommand
from django.db import transaction

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_understaffed_watch_mail import (
    ShiftUnderstaffedWatchEmailBuilder,
)
from tapir.shifts.models import ShiftWatch
from tapir.shifts.utils import get_current_shiftwatch


class Command(BaseCommand):
    help = "Sends emails to interested members that a certain shift is understaffed"

    def handle(self, *args, **options):
        for shift_watch_data in get_current_shiftwatch():
            if (
                shift_watch_data.shift.get_valid_attendances().count()
                < shift_watch_data.shift.get_num_required_attendances()
            ):
                self.send_shift_understaffed_mail(shift_watch_data)

    @staticmethod
    def send_shift_understaffed_mail(shift_watches: ShiftWatch):
        for shift_watch in shift_watches.objects.select_related("user", "shift"):
            with transaction.atomic():
                email_builder = ShiftUnderstaffedWatchEmailBuilder(
                    shift=shift_watch.shift
                )
                SendMailService.send_to_tapir_user(
                    actor=None,
                    recipient=shift_watch.user,
                    email_builder=email_builder,
                )
                shift_watch.notification_sent = True
                shift_watch.save()
            time.sleep(0.1)

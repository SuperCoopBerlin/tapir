import datetime
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts import config
from tapir.shifts.emails.shift_understaffed_watch_mail import (
    ShiftUnderstaffedEmailBuilder,
)
from tapir.shifts.models import ShiftWatch
from tapir.shifts.utils import get_current_shiftwatch


class Command(BaseCommand):
    help = "Sends  emails to every member that a certain shift is understaffed"

    def handle(self, *args, **options):
        for shift_watch_data in get_current_shiftwatch():
            self.send_shift_understaffed_mail(shift_watch_data)

    @staticmethod
    def send_shift_understaffed_mail(shift_watches: ShiftWatch):
        for shift_watch in shift_watches.objects.select_related("user", "shift"):
            # TODO Testen dass die Schicht auch unterbesetzt ist!
            with transaction.atomic():
                email_builder = ShiftUnderstaffedEmailBuilder(shift=shift_watch.shift)
                SendMailService.send_to_tapir_user(
                    actor=None,
                    recipient=shift_watch.user,
                    email_builder=email_builder,
                )
                shift_watch.notification_sent = True
                shift_watch.save()
            time.sleep(0.1)

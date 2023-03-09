import datetime
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tapir.shifts import config
from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmail
from tapir.shifts.models import ShiftUserData, ShiftAttendance
from tapir.shifts.services.frozen_status_service import FrozenStatusService


class Command(BaseCommand):
    help = "Check all members and freeze them or unfreeze them if required. Also sends emails depending on those changes."

    def handle(self, *args, **options):
        ### for member in members:
        ### if must be frozen : freeze
        ### if may get frozen : warn
        ### if must be unfrozen : unfreeze
        for shift_user_data in ShiftUserData.objects.all():
            if FrozenStatusService.should_freeze_member(shift_user_data):
                FrozenStatusService.freeze_member_and_send_email(
                    shift_user_data, actor=None
                )
                continue

    @staticmethod
    def send_shift_reminder_for_user(shift_user_data: ShiftUserData):
        for attendance in ShiftAttendance.objects.with_valid_state().filter(
            user=shift_user_data.user,
            slot__shift__start_time__gte=timezone.now(),
            slot__shift__start_time__lte=timezone.now()
            + datetime.timedelta(days=config.REMINDER_EMAIL_DAYS_BEFORE_SHIFT),
            reminder_email_sent=False,
        ):
            with transaction.atomic():
                mail = ShiftReminderEmail(shift=attendance.slot.shift)
                mail.send_to_tapir_user(actor=None, recipient=attendance.user)

                attendance.reminder_email_sent = True
                attendance.save()
            time.sleep(0.1)

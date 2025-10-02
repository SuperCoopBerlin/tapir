import datetime
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts import config
from tapir.shifts.emails.second_shift_reminder_email import (
    SecondShiftReminderEmailBuilder,
)
from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmailBuilder
from tapir.shifts.models import ShiftUserData, ShiftAttendance


class Command(BaseCommand):
    help = "Sends shift reminder emails to every member that has a shift in the coming week"

    def handle(self, *args, **options):
        for shift_user_data in ShiftUserData.objects.all():
            if config.SECOND_REMINDER_EMAIL_DAYS_BEFORE_SHIFT is not None:
                self.send_second_shift_reminder_for_user(shift_user_data)
            self.send_shift_reminder_for_user(shift_user_data)

    @staticmethod
    def send_shift_reminder_for_user(shift_user_data: ShiftUserData):
        for attendance in ShiftAttendance.objects.with_valid_state().filter(
            user=shift_user_data.user,
            slot__shift__start_time__gte=timezone.now(),
            slot__shift__start_time__lte=timezone.now()
            + datetime.timedelta(days=config.REMINDER_EMAIL_DAYS_BEFORE_SHIFT),
            reminder_email_sent=False,
            second_reminder_email_sent=False,
        ):
            with transaction.atomic():
                email_builder = ShiftReminderEmailBuilder(shift=attendance.slot.shift)
                SendMailService.send_to_tapir_user(
                    actor=None, recipient=attendance.user, email_builder=email_builder
                )

                attendance.reminder_email_sent = True
                attendance.save()
            time.sleep(0.1)

    @staticmethod
    def send_second_shift_reminder_for_user(shift_user_data: ShiftUserData):
        for attendance in ShiftAttendance.objects.with_valid_state().filter(
            user=shift_user_data.user,
            slot__shift__start_time__gte=timezone.now(),
            slot__shift__start_time__lte=timezone.now()
            + datetime.timedelta(days=config.SECOND_REMINDER_EMAIL_DAYS_BEFORE_SHIFT),
            second_reminder_email_sent=False,
        ):
            with transaction.atomic():
                email_builder = SecondShiftReminderEmailBuilder(
                    shift=attendance.slot.shift
                )
                SendMailService.send_to_tapir_user(
                    actor=None, recipient=attendance.user, email_builder=email_builder
                )

                attendance.second_reminder_email_sent = True
                attendance.save()
            time.sleep(0.1)

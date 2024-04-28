import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.emails.shift_understaffed_mail import ShiftUnderstaffedEmail
from tapir.shifts.models import ShiftUserData, Shift


class Command(BaseCommand):
    help = "Sends shift reminder emails to every member that has a shift in the coming week"

    def handle(self, *args, **options):
        self.send_shift_understaffed_warnings_for_user()

    @staticmethod
    def send_shift_understaffed_warnings_for_user():
        shifts = Shift.objects.filter(
            start_time__lte=timezone.now() + F("warning_time"),
            start_time__gte=timezone.now(),
            has_been_warned=False,
        )
        understaffed_shifts = [
            shift
            for shift in shifts
            if shift.get_num_required_attendances() > len(shift.get_valid_attendances())
        ]
        for user in TapirUser.objects.filter(
            wanted_emails__contains=["tapir.shifts.shift_understaffed_mail"]
        ):
            with transaction.atomic():
                mail = ShiftUnderstaffedEmail(shifts=understaffed_shifts)
                mail.send_to_tapir_user(actor=None, recipient=user)
                time.sleep(0.1)
        for shift in understaffed_shifts:
            shift.has_been_warned = True
            shift.save()
            time.sleep(0.1)
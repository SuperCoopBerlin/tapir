from django.core.management.base import BaseCommand
from tapir.shifts.models import ShiftUserData


class Command(BaseCommand):
    help = "Sends shift reminder emails to every member that has a shift in the coming week"

    def handle(self, *args, **options):
        for shift_user_data in ShiftUserData.objects.all():
            shift_user_data.send_shift_reminder_emails()

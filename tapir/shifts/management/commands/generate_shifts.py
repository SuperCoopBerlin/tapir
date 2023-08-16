import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from tapir.shifts.utils import generate_shifts_up_to

GENERATE_UP_TO = datetime.timedelta(days=200)


class Command(BaseCommand):
    help = f"Generate shifts for the upcoming {GENERATE_UP_TO} days"

    def handle(self, *args, **options):
        generate_shifts_up_to(timezone.now().date() + GENERATE_UP_TO)

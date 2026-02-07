from django.core.management.base import BaseCommand
from django.utils import timezone

from tapir.shifts.config import GENERATE_UP_TO
from tapir.shifts.services.shift_generator import ShiftGenerator


class Command(BaseCommand):
    help = f"Generate shifts for the upcoming {GENERATE_UP_TO} days"

    def handle(self, *args, **options):
        ShiftGenerator.generate_shifts_up_to(
            end_date=timezone.now().date() + GENERATE_UP_TO
        )

import datetime

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from tapir.shifts.models import ShiftCycleEntry, ShiftTemplateGroup, Shift
from tapir.shifts.utils import generate_shifts_up_to
from tapir.utils.shortcuts import get_monday

GENERATE_UP_TO = datetime.timedelta(days=200)


class Command(BaseCommand):
    help = f"Generate shifts for the upcoming {GENERATE_UP_TO} days"

    def handle(self, *args, **options):
        generate_shifts_up_to(datetime.date.today() + GENERATE_UP_TO)

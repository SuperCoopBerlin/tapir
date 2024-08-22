import datetime

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from tapir.shifts.models import ShiftCycleEntry, ShiftTemplateGroup, Shift
from tapir.shifts.services.shift_cycle_service import ShiftCycleService
from tapir.utils.shortcuts import get_monday


class Command(BaseCommand):
    help = "If a new cycle has started, remove one shift point from all active members."

    def handle(self, *args, **options):
        next_cycle_start_date = ShiftCycleService.get_next_cycle_start_date()

        if next_cycle_start_date is None:
            return

        ShiftCycleService.apply_cycles_from(next_cycle_start_date)

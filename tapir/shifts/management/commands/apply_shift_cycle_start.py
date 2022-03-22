import datetime

from django.core.management.base import BaseCommand
from django.db.models import Max

from tapir.shifts.models import ShiftCycleEntry, ShiftTemplateGroup, Shift
from tapir.utils.shortcuts import get_monday


class Command(BaseCommand):
    help = "If a new cycle has started, remove one shift point from all active members."

    def handle(self, *args, **options):
        if ShiftCycleEntry.objects.exists():
            last_cycle_date: datetime.date = ShiftCycleEntry.objects.aggregate(
                Max("cycle_start_date")
            )["cycle_start_date__max"]
            new_cycle_start_date = last_cycle_date + datetime.timedelta(
                days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
            )
        else:
            new_cycle_start_date = self.get_first_cycle_start_date()

        if new_cycle_start_date is None:
            return

        if datetime.date.today() >= new_cycle_start_date:
            ShiftCycleEntry.apply_cycle_start(new_cycle_start_date)

    @staticmethod
    def get_first_cycle_start_date():
        first_shift = (
            Shift.objects.filter(
                shift_template__group=ShiftTemplateGroup.objects.first()
            )
            .order_by("start_time")
            .first()
        )
        if not first_shift:
            return None

        return get_monday(first_shift.start_time.date())

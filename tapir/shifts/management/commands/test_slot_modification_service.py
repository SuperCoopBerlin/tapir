import datetime

from django.core.management.base import BaseCommand

from tapir.shifts.models import ShiftUserCapability
from tapir.shifts.services.slot_modification_service import SlotModificationService


class Command(BaseCommand):
    def handle(self, *args, **options):
        changes = [
            SlotModificationService.ParameterSet(
                workday_or_weekend="workday",
                time=datetime.time(hour=8, minute=15),
                origin_slot_name=SlotModificationService.SlotNames.WARENANNAHME,
                target_slot_name=None,
                target_capabilities=None,
            ),
            SlotModificationService.ParameterSet(
                workday_or_weekend="weekend",
                time=datetime.time(hour=19, minute=15),
                origin_slot_name=SlotModificationService.SlotNames.ALLGEMEIN,
                target_slot_name=SlotModificationService.SlotNames.KASSE,
                target_capabilities=frozenset([ShiftUserCapability.CASHIER]),
            ),
        ]
        SlotModificationService.apply_changes(changes)

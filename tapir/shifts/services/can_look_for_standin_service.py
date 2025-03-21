from django.utils import timezone

from tapir.shifts.models import ShiftSlot


class CanLookForStandinService:
    @staticmethod
    def can_look_for_a_standin(slot: ShiftSlot):
        return slot.shift.start_time > timezone.now()

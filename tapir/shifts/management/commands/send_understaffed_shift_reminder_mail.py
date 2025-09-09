import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from send_shift_watch_mail import Command as SendShiftWatchCommand
from tapir.shifts.management.commands.send_shift_watch_mail import get_staffing_status
from tapir.shifts.models import ShiftWatch, StaffingStatusChoices


class Command(BaseCommand):
    help = "Sent as reminder to a member that a shift is still understaffed."

    def handle(self, *args, **options):
        tomorrow = timezone.now().date() + timedelta(days=1)
        shifts_tomorrow = ShiftWatch.objects.filter(shift__end_time__date=tomorrow)

        for shift_watch_data in shifts_tomorrow:
            this_valid_slot_ids = [
                s.slot_id for s in shift_watch_data.shift.get_valid_attendances()
            ]
            number_of_available_slots = shift_watch_data.shift.slots.count()
            valid_attendances_count = len(this_valid_slot_ids)
            required_attendances_count = (
                shift_watch_data.shift.get_num_required_attendances()
            )
            current_status = get_staffing_status(
                number_of_available_slots=number_of_available_slots,
                valid_attendances=valid_attendances_count,
                required_attendances=required_attendances_count,
                last_status=shift_watch_data.last_staffing_status,
            )
            if current_status == StaffingStatusChoices.UNDERSTAFFED:
                SendShiftWatchCommand.send_shift_watch_mail(
                    shift_watch_data, staffing_status=StaffingStatusChoices.UNDERSTAFFED
                )

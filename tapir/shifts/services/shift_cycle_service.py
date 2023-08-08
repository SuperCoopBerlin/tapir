import datetime

from django.db import transaction

from tapir.shifts.models import ShiftUserData, ShiftCycleEntry, ShiftAccountEntry
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService


class ShiftCycleService:
    @staticmethod
    def apply_cycle_start(cycle_start_date: datetime.date, shift_user_datas=None):
        if shift_user_datas is None:
            shift_user_datas = ShiftUserData.objects.all()

        for shift_user_data in shift_user_datas:
            if ShiftCycleEntry.objects.filter(
                shift_user_data=shift_user_data, cycle_start_date=cycle_start_date
            ).exists():
                continue

            with transaction.atomic():
                shift_cycle_log = ShiftCycleEntry.objects.create(
                    shift_user_data=shift_user_data, cycle_start_date=cycle_start_date
                )

                credit_requirement = (
                    ShiftExpectationService.get_credit_requirement_for_cycle(
                        shift_user_data, cycle_start_date
                    )
                )
                if credit_requirement <= 0:
                    continue

                shift_account_entry = ShiftAccountEntry.objects.create(
                    user=shift_user_data.user,
                    value=-credit_requirement,
                    date=cycle_start_date,
                    description="Shift cycle starting the "
                    + cycle_start_date.strftime("%d.%m.%y"),
                )
                shift_cycle_log.shift_account_entry = shift_account_entry
                shift_cycle_log.save()

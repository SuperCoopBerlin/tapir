import datetime

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from tapir.shifts.models import (
    ShiftUserData,
    ShiftCycleEntry,
    ShiftAccountEntry,
    Shift,
    ShiftTemplateGroup,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.utils.shortcuts import get_monday


class ShiftCycleService:
    @classmethod
    def apply_cycle_start(cls, cycle_start_date: datetime.date, shift_user_datas=None):
        if shift_user_datas is None:
            shift_user_datas = ShiftUserData.objects.all()

        for shift_user_data in shift_user_datas:
            cls.apply_cycle_start_for_user(shift_user_data, cycle_start_date)

    @staticmethod
    @transaction.atomic
    def apply_cycle_start_for_user(
        shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        if ShiftCycleEntry.objects.filter(
            shift_user_data=shift_user_data, cycle_start_date=cycle_start_date
        ).exists():
            return

        shift_cycle_log = ShiftCycleEntry.objects.create(
            shift_user_data=shift_user_data, cycle_start_date=cycle_start_date
        )

        credit_requirement = ShiftExpectationService.get_credit_requirement_for_cycle(
            shift_user_data, cycle_start_date
        )
        if credit_requirement <= 0:
            return

        shift_account_entry = ShiftAccountEntry.objects.create(
            user=shift_user_data.user,
            value=-credit_requirement,
            date=cycle_start_date,
            description="Shift cycle starting the "
            + cycle_start_date.strftime("%d.%m.%y"),
        )
        shift_cycle_log.shift_account_entry = shift_account_entry
        shift_cycle_log.save()

    @classmethod
    def get_next_cycle_start_date(cls):
        if not ShiftCycleEntry.objects.exists():
            return cls.get_first_cycle_start_date()

        last_cycle_date: datetime.date = ShiftCycleEntry.objects.aggregate(
            Max("cycle_start_date")
        )["cycle_start_date__max"]

        return last_cycle_date + datetime.timedelta(
            days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
        )

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

    @staticmethod
    def apply_cycles_from(start: datetime.date, end: datetime.date | None = None):
        if end is None:
            end = timezone.now().date()

        new_cycle_start_date = start
        while end >= new_cycle_start_date:
            ShiftCycleService.apply_cycle_start(new_cycle_start_date)
            new_cycle_start_date += datetime.timedelta(
                days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
            )

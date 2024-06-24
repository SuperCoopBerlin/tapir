import datetime

from tapir.shifts.services.slot_modification_service import SlotModificationService
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSlotModificationService(TapirFactoryTestBase):
    def test_pickShiftTemplate_default_includesShiftsWithTheCorrectTime(self):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        excluded_shift = ShiftTemplateFactory.create(
            start_hour=10, start_minute=46, weekday=0
        )
        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )
        selected_shifts = SlotModificationService.pick_shift_templates(parameter_set)
        self.assertIn(included_shift, selected_shifts)
        self.assertNotIn(excluded_shift, selected_shifts)

    def test_pickShiftTemplate_hasExcludedShiftParameter_doesNotIncludeExcludedShift(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        excluded_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )
        selected_shifts = SlotModificationService.pick_shift_templates(
            parameter_set, [excluded_shift.id]
        )
        self.assertIn(included_shift, selected_shifts)
        self.assertNotIn(excluded_shift, selected_shifts)

    def test_pickShiftTemplate_workdayOnly_doesNotIncludeWeekendShift(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        excluded_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=5
        )
        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )
        selected_shifts = SlotModificationService.pick_shift_templates(
            parameter_set, [excluded_shift.id]
        )
        self.assertIn(included_shift, selected_shifts)
        self.assertNotIn(excluded_shift, selected_shifts)

    def test_pickShiftTemplate_weekendOnly_doesNotIncludeWorkdayShift(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=5
        )
        excluded_shift = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WEEKEND,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )
        selected_shifts = SlotModificationService.pick_shift_templates(
            parameter_set, [excluded_shift.id]
        )
        self.assertIn(included_shift, selected_shifts)
        self.assertNotIn(excluded_shift, selected_shifts)

import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
    ShiftSlot,
    ShiftUserCapability,
)
from tapir.shifts.services.slot_modification_service import SlotModificationService
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSlotModificationService(TapirFactoryTestBase):
    def test_pickShiftTemplate_default_includesShiftsWithTheCorrectTime(self):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift_template = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        excluded_shift_template = ShiftTemplateFactory.create(
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
        self.assertIn(included_shift_template, selected_shifts)
        self.assertNotIn(excluded_shift_template, selected_shifts)

    def test_pickShiftTemplate_hasExcludedShiftId_doesNotIncludeExcludedShift(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift_template = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        excluded_shift_template = ShiftTemplateFactory.create(
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
            parameter_set, [excluded_shift_template.id]
        )
        self.assertIn(included_shift_template, selected_shifts)
        self.assertNotIn(excluded_shift_template, selected_shifts)

    def test_pickShiftTemplate_workdayOnly_doesNotIncludeWeekendShift(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift_template = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=0
        )
        excluded_shift_template = ShiftTemplateFactory.create(
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
            parameter_set, [excluded_shift_template.id]
        )
        self.assertIn(included_shift_template, selected_shifts)
        self.assertNotIn(excluded_shift_template, selected_shifts)

    def test_pickShiftTemplate_weekendOnly_doesNotIncludeWorkdayShift(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        included_shift_template = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour, start_minute=targeted_time.minute, weekday=5
        )
        excluded_shift_template = ShiftTemplateFactory.create(
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
            parameter_set, [excluded_shift_template.id]
        )
        self.assertIn(included_shift_template, selected_shifts)
        self.assertNotIn(excluded_shift_template, selected_shifts)

    def test_pickSlotTemplateFromShift_default_returnsSlotWithCorrectName(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour,
            start_minute=targeted_time.minute,
            weekday=0,
            nb_slots=2,
        )

        included_slot = shift_template.slot_templates.first()
        excluded_slot = shift_template.slot_templates.last()

        included_slot.name = "yes"
        included_slot.save()
        excluded_slot.name = "no"
        excluded_slot.save()

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="yes",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )

        selected_slots = SlotModificationService.pick_slot_template_from_shift_template(
            parameter_set, shift_template
        )

        self.assertEqual(included_slot, selected_slots)

    def test_pickSlotTemplateFromShift_lookForSlotThatDoesntExist_raisesError(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour,
            start_minute=targeted_time.minute,
            weekday=0,
            nb_slots=2,
        )

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="does_not_exist",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )

        with self.assertRaises(ShiftSlotTemplate.DoesNotExist):
            SlotModificationService.pick_slot_template_from_shift_template(
                parameter_set, shift_template
            )

    def test_pickSlotTemplateFromShift_onlyOneSlotWithName_returnsTheSlotEvenIfItIsOccupied(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour,
            start_minute=targeted_time.minute,
            weekday=0,
            nb_slots=1,
        )
        slot_template = shift_template.slot_templates.get()
        ShiftAttendanceTemplate.objects.create(
            user=TapirUserFactory.create(),
            slot_template=slot_template,
        )

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name=slot_template.name,
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )

        self.assertEqual(
            slot_template,
            SlotModificationService.pick_slot_template_from_shift_template(
                parameter_set, shift_template
            ),
        )

    def test_pickSlotTemplateFromShift_someSlotsOccupied_returnsANotOccupiedSlot(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour,
            start_minute=targeted_time.minute,
            weekday=0,
            nb_slots=3,
        )

        unoccupied_slot = None
        for index, slot_template in enumerate(shift_template.slot_templates.all()):
            slot_template.name = "yes"
            slot_template.save()

            if index == 1:
                unoccupied_slot = slot_template
                continue

            ShiftAttendanceTemplate.objects.create(
                user=TapirUserFactory.create(),
                slot_template=slot_template,
            )

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="yes",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )

        self.assertEqual(
            unoccupied_slot,
            SlotModificationService.pick_slot_template_from_shift_template(
                parameter_set, shift_template
            ),
        )

    def test_pickSlotTemplateFromShift_allSlotsOccupied_returnsAnOccupiedSlot(
        self,
    ):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_hour=targeted_time.hour,
            start_minute=targeted_time.minute,
            weekday=0,
            nb_slots=3,
        )

        shift_template.slot_templates.update(name="yes")
        for index, slot_template in enumerate(shift_template.slot_templates.all()):
            ShiftAttendanceTemplate.objects.create(
                user=TapirUserFactory.create(),
                slot_template=slot_template,
            )

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="yes",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )

        self.assertIn(
            SlotModificationService.pick_slot_template_from_shift_template(
                parameter_set, shift_template
            ),
            shift_template.slot_templates.all(),
        )

    def test_applyChange_targetNameIsNone_slotTemplateAndGeneratedSlotsGetDeleted(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_template.create_shift(timezone.now().date())
        slot_template_to_delete = shift_template.slot_templates.get()

        self.assertEqual(1, ShiftSlot.objects.count())
        self.assertEqual(1, ShiftSlotTemplate.objects.count())

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name=None,
            target_capabilities=None,
        )

        SlotModificationService.apply_change(parameter_set, slot_template_to_delete)

        self.assertFalse(ShiftSlot.objects.exists())
        self.assertFalse(ShiftSlotTemplate.objects.exists())

    def test_applyChange_targetNameIsSet_slotTemplateAndGeneratedSlotsGetRenamed(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_template.create_shift(timezone.now().date())
        slot_template_to_rename = shift_template.slot_templates.get()

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name="new_name",
            target_capabilities=None,
        )

        SlotModificationService.apply_change(parameter_set, slot_template_to_rename)

        self.assertEqual("new_name", ShiftSlot.objects.get().name)
        self.assertEqual("new_name", ShiftSlotTemplate.objects.get().name)

    def test_applyChange_targetCapabilitiesIsNone_capabilitiesNotAffected(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_template.create_shift(timezone.now().date())
        slot_template = shift_template.slot_templates.get()

        capabilities = [ShiftUserCapability.CASHIER]
        slot_template.required_capabilities = capabilities
        slot_template.save()
        slot_template.generated_slots.update(required_capabilities=capabilities)

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name="new_name",
            target_capabilities=None,
        )

        SlotModificationService.apply_change(parameter_set, slot_template)

        self.assertEqual(capabilities, ShiftSlot.objects.get().required_capabilities)
        self.assertEqual(
            capabilities, ShiftSlotTemplate.objects.get().required_capabilities
        )

    def test_applyChange_targetCapabilitiesIsEmpty_capabilitiesNotRequiredAnymore(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_template.create_shift(timezone.now().date())
        slot_template = shift_template.slot_templates.get()

        capabilities = [ShiftUserCapability.CASHIER]
        slot_template.required_capabilities = capabilities
        slot_template.save()
        slot_template.generated_slots.update(required_capabilities=capabilities)

        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name="new_name",
            target_capabilities=frozenset([]),
        )

        SlotModificationService.apply_change(parameter_set, slot_template)

        self.assertEqual([], ShiftSlot.objects.get().required_capabilities)
        self.assertEqual([], ShiftSlotTemplate.objects.get().required_capabilities)

    def test_applyChange_targetCapabilitiesIsNotEmpty_capabilitiesUpdated(self):
        targeted_time = datetime.time(hour=10, minute=45)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_template.create_shift(timezone.now().date())
        slot_template = shift_template.slot_templates.get()

        capabilities_before = [ShiftUserCapability.CASHIER]
        slot_template.required_capabilities = capabilities_before
        slot_template.save()
        slot_template.generated_slots.update(required_capabilities=capabilities_before)

        capabilities_after = [
            ShiftUserCapability.RED_CARD,
            ShiftUserCapability.MEMBER_OFFICE,
        ]
        parameter_set = SlotModificationService.ParameterSet(
            origin_slot_name="",
            workday_or_weekend=SlotModificationService.WORKDAY,
            time=targeted_time,
            target_slot_name="new_name",
            target_capabilities=frozenset(capabilities_after),
        )

        SlotModificationService.apply_change(parameter_set, slot_template)

        self.assertEqual(
            capabilities_after, ShiftSlot.objects.get().required_capabilities
        )
        self.assertEqual(
            capabilities_after, ShiftSlotTemplate.objects.get().required_capabilities
        )

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendance, ShiftAttendanceTemplate
from tapir.shifts.tests.factories import (
    CapabilityFactory,
    ShiftFactory,
    ShiftTemplateFactory,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestRegisteredToABCDShiftSlotWithCapability(TapirFactoryTestBase):
    def test_registeredToABCDShiftSlotWithCapability_isRegistered_inQuerySet(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create(translations=["en"])

        shift_template = ShiftTemplateFactory.create()

        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        slot_template.save()
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_abcd_shift_slot_with_capability(
            capability
        )

        self.assertIn(user, result)

    def test_registeredToABCDShiftSlotWithCapability_isNotRegistered_notInQuerySet(
        self,
    ):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create(translations=["en"])
        other_capability = CapabilityFactory.create(translations=["en"])

        shift_template = ShiftTemplateFactory.create()
        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        slot_template.save()
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_abcd_shift_slot_with_capability(
            other_capability
        )

        self.assertNotIn(user, result)

    def test_registeredToShiftSlotWithCapability_isRegistered_inQuerySet(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create(translations=["en"])

        shift = ShiftFactory.create()

        slot = shift.slots.first()
        slot.required_capabilities.set([capability])
        slot.save()
        ShiftAttendance.objects.create(
            user=user,
            slot=slot,
        )

        result = TapirUser.objects.registered_to_shift_slot_with_capability(capability)

        self.assertIn(user, result)

    def test_registeredToShiftSlotWithCapability_isNotRegistered_notInQuerySet(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create(translations=["en"])
        other_capability = CapabilityFactory.create(translations=["en"])

        shift_template = ShiftTemplateFactory.create()
        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        slot_template.save()
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_shift_slot_with_capability(
            other_capability
        )

        self.assertNotIn(user, result)

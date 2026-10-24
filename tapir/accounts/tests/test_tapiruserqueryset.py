from django.test import TestCase
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendanceTemplate
from tapir.shifts.tests.factories import CapabilityFactory, ShiftTemplateFactory


class TestRegisteredToABCDShiftSlotWithCapability(TestCase):
    def test_user_registered_to_shift_slot_with_capability(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create()

        shift_template = ShiftTemplateFactory.create()

        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_abcd_shift_slot_with_capability(
            capability
        )

        self.assertIn(user, result)

    def test_user_not_registered_to_shift_slot_with_capability(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create()
        other_capability = CapabilityFactory.create()

        shift_template = ShiftTemplateFactory.create()
        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_abcd_shift_slot_with_capability(
            other_capability
        )

        self.assertNotIn(user, result)

    def test_user_registered_to_shift_with_capability(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create()

        shift_template = ShiftTemplateFactory.create()

        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_shift_slot_with_capability(capability)

        self.assertIn(user, result)

    def test_user_not_registered_to_shift_with_capability(self):
        user = TapirUserFactory.create()
        capability = CapabilityFactory.create()
        other_capability = CapabilityFactory.create()

        shift_template = ShiftTemplateFactory.create()
        slot_template = shift_template.slot_templates.get()
        slot_template.required_capabilities.set([capability])
        shift_template.create_shift_if_necessary(timezone.now().date())
        ShiftAttendanceTemplate.objects.create(
            user=user,
            slot_template=slot_template,
        )

        result = TapirUser.objects.registered_to_shift_slot_with_capability(
            other_capability
        )

        self.assertNotIn(user, result)

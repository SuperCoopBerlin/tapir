import datetime

from django.urls import reverse
from django.utils import timezone
from tapir.shifts.models import (
    ShiftUserCapability,
    ShiftSlotWarning,
    ShiftSlot,
    ShiftTemplate,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSlotTemplateCreate(TapirFactoryTestBase):
    SLOT_TEMPLATE_CREATE_VIEW = "shifts:create_slot_template"
    SLOT_TEMPLATE_NAME = "A test name"

    def test_creating_a_slot_template_also_creates_the_slot_in_future_shifts(self):
        self.login_as_member_office_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=0)
        shift = shift_template.create_shift_if_necessary(
            timezone.now().date() + datetime.timedelta(days=10)
        )

        required_capabilities = [ShiftUserCapability.SHIFT_COORDINATOR]
        warnings = [ShiftSlotWarning.BREAD_PICKUP_NEEDS_A_VEHICLE]

        response = self.client.post(
            reverse(self.SLOT_TEMPLATE_CREATE_VIEW, args=[shift_template.id]),
            {
                "name": self.SLOT_TEMPLATE_NAME,
                "required_capabilities": required_capabilities,
                "warnings": warnings,
                "check_update_future_shifts": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        shift_template.refresh_from_db()
        self.assertEqual(shift_template.slot_templates.count(), 1)
        shift.refresh_from_db()
        self.assertEqual(shift.slots.count(), 1)

        slot: ShiftSlot = shift.slots.first()
        self.assertEqual(slot.name, self.SLOT_TEMPLATE_NAME)
        self.assertEqual(slot.required_capabilities, required_capabilities)
        self.assertEqual(slot.warnings, warnings)

    def test_normal_user_access_denied(self):
        self.login_as_normal_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create()

        response = self.client.post(
            reverse(self.SLOT_TEMPLATE_CREATE_VIEW, args=[shift_template.id]),
            {"name": self.SLOT_TEMPLATE_NAME},
        )

        self.assertEqual(
            response.status_code,
            403,
            "A user that is not in the member should not have access to shift slot creation.",
        )

    def test_adding_a_slot_to_the_template_does_not_add_a_slot_to_past_shifts(self):
        self.login_as_member_office_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=0)
        shift = shift_template.create_shift_if_necessary(
            timezone.now().date() - datetime.timedelta(days=10)
        )

        response = self.client.post(
            reverse(self.SLOT_TEMPLATE_CREATE_VIEW, args=[shift_template.id]),
            {
                "name": self.SLOT_TEMPLATE_NAME,
                "check_update_future_shifts": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        shift_template.refresh_from_db()
        self.assertEqual(shift_template.slot_templates.count(), 1)
        shift.refresh_from_db()
        self.assertEqual(shift.slots.count(), 0)

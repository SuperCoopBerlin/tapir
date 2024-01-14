import datetime

from django.urls import reverse

from tapir.shifts.models import (
    ShiftUserCapability,
    ShiftSlotWarning,
    ShiftTemplate,
    ShiftSlotTemplate,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSlotTemplateEdit(TapirFactoryTestBase):
    SLOT_TEMPLATE_EDIT_VIEW = "shifts:edit_slot_template"

    def test_edit_a_slot_template_also_affects_future_slots(self):
        self.login_as_member_office_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=1)
        slot_template: ShiftSlotTemplate = shift_template.slot_templates.first()
        slot_template.required_capabilities = []
        slot_template.warnings = []
        slot_template.save()
        shift = shift_template.create_shift(
            timezone.now().today() + datetime.timedelta(days=10)
        )
        slot = shift.slots.first()
        self.assertEqual([], slot.required_capabilities)
        self.assertEqual([], slot.warnings)

        name = "Name after"
        required_capabilities = [ShiftUserCapability.SHIFT_COORDINATOR]
        warnings = [ShiftSlotWarning.BREAD_PICKUP_NEEDS_A_VEHICLE]

        response = self.client.post(
            reverse(self.SLOT_TEMPLATE_EDIT_VIEW, args=[slot_template.id]),
            {
                "name": name,
                "required_capabilities": required_capabilities,
                "warnings": warnings,
                "check_update_future_shifts": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        slot_template.refresh_from_db()
        self.assertEqual(slot_template.name, name)
        self.assertEqual(slot_template.required_capabilities, required_capabilities)
        self.assertEqual(slot_template.warnings, warnings)

        slot.refresh_from_db()
        self.assertEqual(slot.name, name)
        self.assertEqual(slot.required_capabilities, required_capabilities)
        self.assertEqual(slot.warnings, warnings)

    def test_normal_user_access_denied(self):
        self.login_as_normal_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create()

        response = self.client.post(
            reverse(self.SLOT_TEMPLATE_EDIT_VIEW, args=[shift_template.id]),
            {"name": "Name after"},
        )

        self.assertEqual(
            response.status_code,
            403,
            "A user that is not in the member should not have access to slot template edition.",
        )

    def test_editing_a_slot_template_does_not_affect_past_slots(self):
        self.login_as_member_office_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=1)
        slot_template = shift_template.slot_templates.first()
        slot_template.name = "Name before"
        slot_template.save()
        shift = shift_template.create_shift(
            timezone.now().today() - datetime.timedelta(days=10)
        )
        slot = shift.slots.first()
        self.assertEqual("Name before", slot.name)

        response = self.client.post(
            reverse(self.SLOT_TEMPLATE_EDIT_VIEW, args=[shift_template.id]),
            {
                "name": "Name after",
                "check_update_future_shifts": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        slot_template.refresh_from_db()
        self.assertEqual("Name after", slot_template.name)
        shift.refresh_from_db()
        self.assertEqual("Name before", slot.name)

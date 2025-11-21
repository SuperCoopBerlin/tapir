from django.urls import reverse

from tapir.shifts.models import (
    Shift,
    ShiftSlot,
)
from tapir.shifts.tests.factories import (
    ShiftFactory,
    ShiftUserCapabilityFactory,
    ShiftSlotWarningFactory,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSlotCreate(TapirFactoryTestBase):
    SLOT_CREATE_VIEW = "shifts:create_slot"
    SLOT_NAME = "Slot name"

    def test_member_office_can_create_slot(self):
        self.login_as_member_office_user()
        self._assert_can_create_slot()

    def test_shift_manager_can_create_slot(self):
        self.login_as_shift_manager()
        self._assert_can_create_slot()

    def _assert_can_create_slot(self):
        shift: Shift = ShiftFactory.create(nb_slots=0)
        self.assertEqual(shift.slots.count(), 0)

        required_capabilities = [ShiftUserCapabilityFactory.create().id]
        warnings = [ShiftSlotWarningFactory.create().id]

        response = self.client.post(
            reverse(self.SLOT_CREATE_VIEW, args=[shift.id]),
            {
                "name": self.SLOT_NAME,
                "required_capabilities": required_capabilities,
                "warnings": warnings,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(shift.slots.count(), 1)

        slot: ShiftSlot = shift.slots.first()
        self.assertEqual(slot.name, self.SLOT_NAME)
        self.assertEqual(
            list(slot.required_capabilities.values_list("id", flat=True)),
            required_capabilities,
            "difference in capabilities",
        )
        self.assertEqual(
            list(slot.warnings.values_list("id", flat=True)),
            warnings,
            "difference in warnings",
        )

    def test_normal_user_access_denied(self):
        self.login_as_normal_user()

        shift: Shift = ShiftFactory.create(nb_slots=0)

        response = self.client.post(
            reverse(self.SLOT_CREATE_VIEW, args=[shift.id]),
            {"name": self.SLOT_NAME},
            follow=True,
        )

        self.assertEqual(
            response.status_code,
            403,
            "A user that is not in the member should not have access to shift slot creation.",
        )

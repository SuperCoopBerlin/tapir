from django.urls import reverse

from tapir.shifts.models import (
    Shift,
    ShiftUserCapability,
    ShiftSlotWarning,
    ShiftSlot,
)
from tapir.shifts.tests.factories import ShiftFactory
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

        required_capabilities = [ShiftUserCapability.CASHIER]
        warnings = [ShiftSlotWarning.IN_THE_MORNING_EVERYONE_HELPS_STORAGE]

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
        self.assertEqual(slot.required_capabilities, required_capabilities)
        self.assertEqual(slot.warnings, warnings)

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

from datetime import time, timedelta

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftAttendanceTemplate,
    ShiftSlotTemplate,
    ShiftUserCapability,
)
from tapir.utils.tests_utils import LdapEnabledTestCase


class ShiftsTestCase(LdapEnabledTestCase):
    def test_shift_template_update_shift_attendances(self):
        user = TapirUser.objects.create(
            username="ariana.perrin", email="ariana.perrin@supercoop.de"
        )

        shift_template = ShiftTemplate.objects.create(
            start_time=time(15, 00), end_time=time(18, 00)
        )
        slot_template = ShiftSlotTemplate.objects.create(shift_template=shift_template)

        # Create a shift instance
        shift = shift_template.create_shift(
            start_date=timezone.now() + timedelta(days=1)
        )
        self.assertQuerysetEqual(shift.get_attendances().all(), [])

        # Create an attendance for the shift template
        shift_attendance_template = ShiftAttendanceTemplate.objects.create(
            slot_template=slot_template, user=user
        )
        shift_template.update_future_shift_attendances(now=timezone.now())

        # Verify that the already-created shift instance was updated
        self.assertEqual(shift.get_attendances().all()[0].user, user)

    def test_shift_template_can_attend_check_capabilities(self):
        user = TapirUser.objects.create(
            username="ariana.perrin", email="ariana.perrin@supercoop.de"
        )
        shift_template = ShiftTemplate.objects.create(
            start_time=time(15, 00), end_time=time(18, 00)
        )
        slot_template = ShiftSlotTemplate.objects.create(shift_template=shift_template)
        capability = ShiftUserCapability.SHIFT_COORDINATOR
        slot_template.required_capabilities.append(capability)
        self.assertFalse(
            slot_template.user_can_attend(user),
            "User should not be able to attend that shift slot template because they don't have the required capability",
        )
        user.shift_user_data.capabilities.append(capability)
        self.assertTrue(
            slot_template.user_can_attend(user),
            "User should be able to attend that shift slot template",
        )

    def test_shift_can_attend_check_capabilities(self):
        user = TapirUser.objects.create(
            username="ariana.perrin", email="ariana.perrin@supercoop.de"
        )
        shift_template = ShiftTemplate.objects.create(
            start_time=time(15, 00), end_time=time(18, 00)
        )
        ShiftSlotTemplate.objects.create(shift_template=shift_template)
        shift = shift_template.create_shift(
            start_date=timezone.now() + timedelta(days=1)
        )
        slot = shift.slots.all()[0]
        capability = ShiftUserCapability.SHIFT_COORDINATOR
        slot.required_capabilities.append(capability)
        self.assertFalse(
            slot.user_can_attend(user),
            "User should not be able to attend that shift slot because they don't have the required capability",
        )
        user.shift_user_data.capabilities.append(capability)
        self.assertTrue(
            slot.user_can_attend(user),
            "User should be able to attend that shift slot",
        )

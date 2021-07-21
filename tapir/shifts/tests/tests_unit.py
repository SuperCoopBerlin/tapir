from datetime import time, date, datetime

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftSlotTemplate,
)
from tapir.utils.tests_utils import LdapEnabledTestCase


class ShiftsTestCase(LdapEnabledTestCase):
    def test_shift_template_update_shift_attendances(self):
        user1 = TapirUser.objects.create(
            username="ariana.perrin", email="ariana.perrin@supercoop.de"
        )
        user2 = TapirUser.objects.create(
            username="nicolas.vicente", email="nicolas.vicente@supercoop.de"
        )

        shift_template = ShiftTemplate.objects.create(
            start_time=time(15, 00), end_time=time(18, 00)
        )
        slot_template = ShiftSlotTemplate.objects.create(shift_template=shift_template)

        # Create a shift instance
        shift = shift_template.create_shift(start_date=date(2021, 3, 24))
        self.assertQuerysetEqual(shift.get_attendances().all(), [])

        # Create an attendance for the shift template
        ShiftAttendanceTemplate.objects.create(slot_template=slot_template, user=user1)
        shift_template.update_future_shift_attendances(
            now=datetime(2021, 3, 24, 0, 0, 0)
        )

        # Verify that the already-created shift instance was updated
        self.assertEqual(shift.get_attendances().all()[0].user, user1)

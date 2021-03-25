from django.test import TestCase
from datetime import time, date

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftTemplate,
    Shift,
    ShiftAttendanceTemplate,
    ShiftAttendance,
)


class ShiftsTestCase(TestCase):
    fixtures = ["accounts.json"]

    def test_shift_template_update_shift_attendances(self):
        user1 = TapirUser.objects.get(username="karin.ritter")
        user2 = TapirUser.objects.get(username="norman.ritter")

        st = ShiftTemplate.objects.create(
            start_time=time(15, 00), end_time=time(18, 00)
        )
        s = st.create_shift(start_date=date(2021, 3, 24))
        self.assertQuerysetEqual(s.attendances.all(), [])

        ShiftAttendance.objects.create(shift=s, user=user2)
        ShiftAttendanceTemplate.objects.create(shift_template=st, user=user1)

        # We expect user2 to be removed and user1 to be added
        s.update_attendances_from_shift_template()
        self.assertEqual(s.attendances.all()[0].user, user1)

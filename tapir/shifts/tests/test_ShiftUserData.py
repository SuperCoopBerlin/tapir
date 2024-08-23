from django.test import SimpleTestCase

from tapir.shifts.models import ShiftAttendanceMode, ShiftUserData


class TestShiftUserData(SimpleTestCase):
    def test_canShop_userWithRegularAttendanceMode_canShop(self):
        shift_user_data = ShiftUserData(attendance_mode=ShiftAttendanceMode.REGULAR)
        self.assertTrue(shift_user_data.can_shop())

    def test_canShop_userWithFrozenAttendanceMode_cannotShop(self):
        shift_user_data = ShiftUserData(attendance_mode=ShiftAttendanceMode.FROZEN)
        self.assertFalse(shift_user_data.can_shop())

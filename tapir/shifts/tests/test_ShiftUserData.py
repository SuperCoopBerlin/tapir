from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendanceMode
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftUserData(TapirFactoryTestBase):
    def test_canShop_userWithRegularAttendanceMode_canShop(self):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        tapir_user.shift_user_data.save()
        tapir_user.shift_user_data.refresh_from_db()
        self.assertTrue(tapir_user.shift_user_data.can_shop())

    def test_canShop_userWithFrozenAttendanceMode_cannotShop(self):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        tapir_user.shift_user_data.save()
        tapir_user.shift_user_data.refresh_from_db()
        self.assertFalse(tapir_user.shift_user_data.can_shop())

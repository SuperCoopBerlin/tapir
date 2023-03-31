from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAccountEntry, ShiftAttendanceMode
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftUserData(TapirFactoryTestBase):
    def test_canShop_userWithPositiveBalance_canShop(self):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(user=tapir_user, date=timezone.now(), value=2)
        self.assertTrue(tapir_user.shift_user_data.can_shop())

    def test_canShop_userWithNegativeBalance_cannotShop(self):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(user=tapir_user, date=timezone.now(), value=-2)
        self.assertFalse(tapir_user.shift_user_data.can_shop())

    def test_canShop_userWithFrozenAttendanceMode_cannotShop(self):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        ShiftAccountEntry.objects.create(user=tapir_user, date=timezone.now(), value=2)
        self.assertFalse(tapir_user.shift_user_data.can_shop())

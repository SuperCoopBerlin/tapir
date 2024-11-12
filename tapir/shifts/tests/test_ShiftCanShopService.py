from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.services.shift_can_shop_service import ShiftCanShopService
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCanShopService(TapirFactoryTestBase):
    def test_canShop_userNotFrozen_canShop(self):
        shift_user_data = TapirUserFactory.create().shift_user_data
        shift_user_data.is_frozen = False
        shift_user_data.save()
        self.assertTrue(ShiftCanShopService.can_shop(shift_user_data))

    def test_canShop_userFrozen_cannotShop(self):
        shift_user_data = TapirUserFactory.create().shift_user_data
        shift_user_data.is_frozen = True
        shift_user_data.save()
        self.assertFalse(ShiftCanShopService.can_shop(shift_user_data))

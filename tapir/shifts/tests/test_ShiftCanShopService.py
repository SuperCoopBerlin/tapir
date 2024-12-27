import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.shift_can_shop_service import ShiftCanShopService
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCanShopService(TapirFactoryTestBase):
    REFERENCE_TIME = timezone.make_aware(datetime.datetime(year=2023, month=2, day=12))

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

    def test_annotateShareOwnerQuerysetWithCanShopAtDatetime_memberIsNotFrozen_returnsTrue(
        self,
    ):
        TapirUserFactory.create()
        ShiftUserData.objects.update(is_frozen=False)

        queryset = (
            ShiftCanShopService.annotate_share_owner_queryset_with_can_shop_at_datetime(
                ShareOwner.objects.all(), self.REFERENCE_TIME
            )
        )

        self.assertEqual(1, queryset.count())
        self.assertTrue(
            getattr(queryset.first(), ShiftCanShopService.ANNOTATION_SHIFT_CAN_SHOP)
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.first(),
                ShiftCanShopService.ANNOTATION_SHIFT_CAN_SHOP_DATE_CHECK,
            ),
        )

    def test_annotateShareOwnerQuerysetWithCanShopAtDatetime_memberIsFrozen_returnsFalse(
        self,
    ):
        TapirUserFactory.create()
        ShiftUserData.objects.update(is_frozen=True)

        queryset = (
            ShiftCanShopService.annotate_share_owner_queryset_with_can_shop_at_datetime(
                ShareOwner.objects.all(), self.REFERENCE_TIME
            )
        )

        self.assertFalse(
            getattr(queryset.first(), ShiftCanShopService.ANNOTATION_SHIFT_CAN_SHOP)
        )

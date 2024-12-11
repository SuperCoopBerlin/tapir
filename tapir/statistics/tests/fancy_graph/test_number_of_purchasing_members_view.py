import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.statistics.views.fancy_graph.number_of_purchasing_members_view import (
    NumberOfPurchasingMembersAtDateView,
)
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestNumberOfPurchasingMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def create_member_that_can_shop(self):
        tapir_user = TapirUserFactory.create(share_owner__is_investing=False)
        ShareOwnership.objects.update(start_date=self.REFERENCE_TIME.date())
        self.assertTrue(
            MemberCanShopService.can_shop(tapir_user.share_owner, self.REFERENCE_TIME)
        )

    def test_calculateDatapoint_memberCantShop_notCounted(self):
        self.create_member_that_can_shop()
        ShareOwner.objects.update(is_investing=True)

        result = NumberOfPurchasingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberCanShop_counted(self):
        self.create_member_that_can_shop()

        result = NumberOfPurchasingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

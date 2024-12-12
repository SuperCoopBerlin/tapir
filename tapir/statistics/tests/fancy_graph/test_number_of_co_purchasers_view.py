import datetime

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.statistics.views.fancy_graph.number_of_co_purchasers_view import (
    NumberOfCoPurchasersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_can_shop,
)


class TestNumberOfCoPurchasersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberHasCoPurchaserButCannotShop_notCounted(self):
        create_member_that_can_shop(self, self.REFERENCE_TIME)
        ShareOwner.objects.update(is_investing=True)
        TapirUser.objects.update(co_purchaser="A test co-purchaser")

        result = NumberOfCoPurchasersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberCanShopButDoesntHaveACoPurchaser_notCounted(
        self,
    ):
        create_member_that_can_shop(self, self.REFERENCE_TIME)
        TapirUser.objects.update(co_purchaser="")

        result = NumberOfCoPurchasersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsWorkingAndHasCoPurchaser_counted(self):
        create_member_that_can_shop(self, self.REFERENCE_TIME)
        TapirUser.objects.update(co_purchaser="A test co-purchaser")

        result = NumberOfCoPurchasersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

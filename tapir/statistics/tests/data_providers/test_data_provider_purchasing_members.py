import datetime

from django.utils import timezone

from tapir.coop.models import ShareOwner
from tapir.statistics.services.data_providers.data_provider_purchasing_members import (
    DataProviderPurchasingMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_can_shop,
)


class TestDataProviderPurchasingMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberCantShop_notIncluded(self):
        create_member_that_can_shop(self, self.REFERENCE_TIME)
        ShareOwner.objects.update(is_investing=True)

        queryset = DataProviderPurchasingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberCanShop_included(self):
        tapir_user = create_member_that_can_shop(self, self.REFERENCE_TIME)

        queryset = DataProviderPurchasingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

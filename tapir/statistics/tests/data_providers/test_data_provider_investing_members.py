import datetime

from django.utils import timezone

from tapir.coop.models import ShareOwnership
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.services.data_providers.data_provider_investing_members import (
    DataProviderInvestingMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderInvestingMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberIsNotInvesting_notIncluded(self):
        ShareOwnerFactory.create(is_investing=False)

        queryset = DataProviderInvestingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsInvesting_included(self):
        share_owner = ShareOwnerFactory.create(is_investing=True)
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

        queryset = DataProviderInvestingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(share_owner, queryset)

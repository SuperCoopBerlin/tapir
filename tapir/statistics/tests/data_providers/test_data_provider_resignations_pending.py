import datetime

from django.utils import timezone

from tapir.coop.tests.factories import MembershipResignationFactory
from tapir.statistics.services.data_providers.data_provider_resignations_pending import (
    DataProviderResignationsPending,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderPendingResignations(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_resignationIsPayedOut_notIncluded(self):
        MembershipResignationFactory.create(
            cancellation_date=datetime.date(year=2022, month=5, day=1),
            pay_out_day=datetime.date(year=2022, month=6, day=14),
        )

        queryset = DataProviderResignationsPending.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_resignationIsPending_included(self):
        resignation = MembershipResignationFactory.create(
            cancellation_date=datetime.date(year=2022, month=5, day=1),
            pay_out_day=datetime.date(year=2022, month=6, day=16),
        )

        queryset = DataProviderResignationsPending.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(resignation.share_owner, queryset)

    def test_getQueryset_resignationIsInTheFuture_included(self):
        MembershipResignationFactory.create(
            cancellation_date=datetime.date(year=2022, month=6, day=16),
            pay_out_day=datetime.date(year=2028, month=6, day=14),
        )

        queryset = DataProviderResignationsPending.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

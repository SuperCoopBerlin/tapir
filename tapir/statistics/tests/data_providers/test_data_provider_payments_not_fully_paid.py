import datetime

from django.utils import timezone

from tapir.coop.models import IncomingPayment
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.coop.tests.incoming_payment_factory import IncomingPaymentFactory
from tapir.statistics.services.data_providers.data_provider_payments_not_fully_paid import (
    DataProviderPaymentsNotFullyPaid,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderPaymentsNotFullyPaid(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberHasPaidEnough_notIncluded(self):
        share_owner = ShareOwnerFactory.create(nb_shares=1)
        IncomingPaymentFactory.create(
            credited_member=share_owner, amount=110, payment_date=self.REFERENCE_TIME
        )

        queryset = DataProviderPaymentsNotFullyPaid.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberHasNotPaidEnough_included(self):
        share_owner = ShareOwnerFactory.create(nb_shares=1)
        IncomingPaymentFactory.create(
            credited_member=share_owner, amount=90, payment_date=self.REFERENCE_TIME
        )

        queryset = DataProviderPaymentsNotFullyPaid.get_queryset(self.REFERENCE_TIME)

        self.assertGreaterEqual(1, queryset.count())
        self.assertIn(share_owner, queryset)

    def test_getQueryset_memberHasNotPaidAtAll_included(self):
        share_owner = ShareOwnerFactory.create(nb_shares=1)
        self.assertEqual(0, IncomingPayment.objects.count())

        queryset = DataProviderPaymentsNotFullyPaid.get_queryset(self.REFERENCE_TIME)

        self.assertGreaterEqual(1, queryset.count())
        self.assertIn(share_owner, queryset)

import datetime

from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.coop.services.payment_status_service import PaymentStatusService
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.coop.tests.incoming_payment_factory import IncomingPaymentFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestPaymentStatusService(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)
        self.create_noise()

    @staticmethod
    def create_noise():
        # add a few other members to make sure each member gets annotated their own data
        for _ in range(3):
            share_owner = ShareOwnerFactory.create(nb_shares=10)
            IncomingPaymentFactory.create_batch(3, credited_member=share_owner)

    def test_annotateWithPaymentsAtDate_default_returnsCorrectValue(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=123,
            payment_date=datetime.date(year=2023, month=6, day=2),
        )
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=123,
            payment_date=datetime.date(year=2023, month=7, day=1),
        )

        annotated = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.all(), datetime.date(year=2023, month=8, day=15)
        )

        self.assertEqual(
            123 + 123,
            getattr(
                annotated.get(id=share_owner.id),
                PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE,
            ),
        )

    def test_annotateWithPaymentsAtDate_somePaymentsHappenedAfterTheDate_onlyPaymentsBeforeTheDateCounted(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=123,
            payment_date=datetime.date(year=2023, month=6, day=2),
        )
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=456,
            payment_date=datetime.date(year=2023, month=7, day=1),
        )

        annotated = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.all(), datetime.date(year=2023, month=6, day=15)
        )

        self.assertEqual(
            123,
            getattr(
                annotated.get(id=share_owner.id),
                PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE,
            ),
        )

    def test_annotateWithPaymentsAtDate_noDateGiven_todayUsedAsDate(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=123,
            payment_date=self.NOW.date() - datetime.timedelta(days=1),
        )
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=456,
            payment_date=self.NOW.date() + datetime.timedelta(days=1),
        )

        annotated = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.all()
        )

        self.assertEqual(
            123,
            getattr(
                annotated.get(id=share_owner.id),
                PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE,
            ),
        )

    def test_annotateWithPaymentsAtDate_someSharesAreNotValidAtDate_countOnlySharesValidAtDate(
        self,
    ):
        share_owner = ShareOwnerFactory.create(nb_shares=0)
        ShareOwnership.objects.create(
            share_owner=share_owner,
            start_date=self.NOW - datetime.timedelta(days=10),
            end_date=None,
        )
        ShareOwnership.objects.create(
            share_owner=share_owner,
            start_date=self.NOW - datetime.timedelta(days=10),
            end_date=self.NOW - datetime.timedelta(days=5),
        )

        annotated = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.all()
        )

        self.assertEqual(
            110,
            getattr(
                annotated.get(id=share_owner.id),
                PaymentStatusService.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE,
            ),
        )

    def test_annotateWithPaymentsAtDate_alsoAnnotatedWithNumberOfShares_returnsCorrectValue(
        self,
    ):
        # if the NumberOfSharesService doesn't use subqueries, the annotations from PaymentStatusService can return wrong values
        share_owner = ShareOwnerFactory.create()
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=123,
            payment_date=datetime.date(year=2023, month=6, day=2),
        )
        IncomingPaymentFactory.create(
            credited_member=share_owner,
            amount=456,
            payment_date=datetime.date(year=2023, month=7, day=1),
        )

        queryset = ShareOwner.objects.all()
        at_date = datetime.date(year=2023, month=8, day=15)
        queryset = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            queryset, at_date
        )
        queryset = PaymentStatusService.annotate_with_payments_at_date(
            queryset, at_date
        )

        for share_owner in queryset.all():
            manual_sum = 0
            for incoming_payment in share_owner.credited_payments.all():
                if incoming_payment.payment_date <= at_date:
                    manual_sum += incoming_payment.amount
            self.assertEqual(
                manual_sum,
                getattr(
                    share_owner,
                    PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE,
                ),
            )

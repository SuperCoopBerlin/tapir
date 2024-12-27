import datetime

from django.utils import timezone

from tapir.coop.tests.factories import MembershipResignationFactory
from tapir.statistics.views.fancy_graph.number_of_created_resignations_view import (
    NumberOfCreatedResignationsInSameMonthView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfCreatedResignationsInSameMonthView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_default_countsOnlyRelevantResignations(self):
        MembershipResignationFactory.create(
            cancellation_date=datetime.date(year=2022, month=5, day=1)
        )
        MembershipResignationFactory.create(
            cancellation_date=datetime.date(year=2022, month=6, day=30)
        )
        MembershipResignationFactory.create(
            cancellation_date=datetime.date(year=2023, month=6, day=30)
        )

        result = NumberOfCreatedResignationsInSameMonthView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

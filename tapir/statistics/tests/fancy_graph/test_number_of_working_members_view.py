import datetime

from django.utils import timezone

from tapir.coop.models import ShareOwner
from tapir.statistics.views.fancy_graph.number_of_working_members_view import (
    NumberOfWorkingMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_is_working,
)


class TestNumberOfWorkingMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberIsWorking_counted(self):
        create_member_that_is_working(self, self.REFERENCE_TIME)

        result = NumberOfWorkingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

    def test_calculateDatapoint_memberIsNotWorking_notCounted(self):
        create_member_that_is_working(self, self.REFERENCE_TIME)
        ShareOwner.objects.update(is_investing=True)

        result = NumberOfWorkingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

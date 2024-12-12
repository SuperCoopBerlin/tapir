import datetime

from django.utils import timezone

from tapir.coop.models import MembershipPause
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.views.fancy_graph.number_of_paused_members_view import (
    NumberOfPausedMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfPausedMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberIsNotPaused_notCounted(self):
        ShareOwnerFactory.create()

        result = NumberOfPausedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsPaused_counted(self):
        share_owner = ShareOwnerFactory.create(is_investing=False)
        MembershipPause.objects.create(
            share_owner=share_owner,
            description="Test",
            start_date=self.REFERENCE_TIME.date(),
        )

        result = NumberOfPausedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

import datetime

from django.utils import timezone

from tapir.coop.models import MemberStatus, MembershipPause
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.views.fancy_graph.number_of_members_view import (
    NumberOfMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfActiveMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberStatusSold_notCounted(self):
        member_sold = ShareOwnerFactory.create(nb_shares=0)
        self.assertEqual(
            MemberStatus.SOLD, member_sold.get_member_status(self.REFERENCE_TIME)
        )

        result = NumberOfMembersAtDateView().calculate_datapoint(self.REFERENCE_TIME)

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberStatusInvesting_counted(self):
        member_investing = ShareOwnerFactory.create(is_investing=True)
        self.assertEqual(
            MemberStatus.INVESTING,
            member_investing.get_member_status(self.REFERENCE_TIME),
        )

        result = NumberOfMembersAtDateView().calculate_datapoint(self.REFERENCE_TIME)

        self.assertEqual(1, result)

    def test_calculateDatapoint_memberStatusPaused_counted(self):
        member_paused = ShareOwnerFactory.create(is_investing=False)
        MembershipPause.objects.create(
            share_owner=member_paused,
            description="Test",
            start_date=self.REFERENCE_TIME.date(),
        )
        self.assertEqual(
            MemberStatus.PAUSED,
            member_paused.get_member_status(self.REFERENCE_TIME),
        )

        result = NumberOfMembersAtDateView().calculate_datapoint(self.REFERENCE_TIME)

        self.assertEqual(1, result)

    def test_calculateDatapoint_memberStatusActive_counted(self):
        member_active = ShareOwnerFactory.create(is_investing=False)
        self.assertEqual(
            MemberStatus.ACTIVE,
            member_active.get_member_status(self.REFERENCE_TIME),
        )

        result = NumberOfMembersAtDateView().calculate_datapoint(self.REFERENCE_TIME)

        self.assertEqual(1, result)

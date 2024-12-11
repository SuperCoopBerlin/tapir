import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftUserData
from tapir.statistics.views.fancy_graph.number_of_frozen_members_view import (
    NumberOfFrozenMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfFrozenMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberIsFrozenButIsNoActive_notCounted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        result = NumberOfFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsActiveButIsNotFrozen_notCounted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShiftUserData.objects.update(is_frozen=False)

        result = NumberOfFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsActiveAndFrozen_counted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShiftUserData.objects.update(is_frozen=True)

        result = NumberOfFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

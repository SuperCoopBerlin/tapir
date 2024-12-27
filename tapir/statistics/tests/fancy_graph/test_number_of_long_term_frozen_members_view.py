import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwnership
from tapir.shifts.models import ShiftUserData, UpdateShiftUserDataLogEntry
from tapir.statistics.views.fancy_graph.number_of_long_term_frozen_members_view import (
    NumberOfLongTermFrozenMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfLongTermFrozenMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberIsNotFrozen_notCounted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=False)

        result = NumberOfLongTermFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsFrozenSinceNotLongEnough_notCounted(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": False},
            new_values={"is_frozen": True},
        )
        log_entry.created_date = self.REFERENCE_TIME - datetime.timedelta(days=150)
        log_entry.save()

        result = NumberOfLongTermFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsFrozenSinceLongEnough_counted(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": False},
            new_values={"is_frozen": True},
        )
        log_entry.created_date = self.REFERENCE_TIME - datetime.timedelta(days=190)
        log_entry.save()

        result = NumberOfLongTermFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

    def test_calculateDatapoint_memberIsFrozenAndHasNoLogs_counted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        result = NumberOfLongTermFrozenMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

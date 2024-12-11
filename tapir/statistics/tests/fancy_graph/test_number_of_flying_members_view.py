import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import CreateShiftAttendanceTemplateLogEntry
from tapir.statistics.views.fancy_graph.number_of_flying_members_view import (
    NumberOfFlyingMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_attendance_template_log_entry_in_the_past,
)


class TestNumberOfFlyingMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberIsFlyingButIsNotWorking_notCounted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )

        result = NumberOfFlyingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsWorkingButIsNotFlying_notCounted(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1)
        )
        create_attendance_template_log_entry_in_the_past(
            CreateShiftAttendanceTemplateLogEntry, tapir_user, self.REFERENCE_TIME
        )

        result = NumberOfFlyingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsWorkingAndFlying_counted(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )

        result = NumberOfFlyingMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

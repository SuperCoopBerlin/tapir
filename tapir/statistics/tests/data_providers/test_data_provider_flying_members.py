import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import CreateShiftAttendanceTemplateLogEntry
from tapir.statistics.services.data_providers.data_provider_flying_members import (
    DataProviderFlyingMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_attendance_template_log_entry_in_the_past,
    create_member_that_is_working,
)


class TestDataProviderFlyingMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberIsFlyingButIsNotWorking_notIncluded(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )

        queryset = DataProviderFlyingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsWorkingButIsNotFlying_notIncluded(self):
        tapir_user = create_member_that_is_working(self, self.REFERENCE_TIME)
        create_attendance_template_log_entry_in_the_past(
            CreateShiftAttendanceTemplateLogEntry, tapir_user, self.REFERENCE_TIME
        )

        queryset = DataProviderFlyingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsWorkingAndFlying_included(self):
        tapir_user = create_member_that_is_working(self, self.REFERENCE_TIME)

        queryset = DataProviderFlyingMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

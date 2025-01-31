import datetime

from django.utils import timezone

from tapir.shifts.models import ShiftAttendance, ShiftExemption
from tapir.shifts.tests.factories import ShiftFactory
from tapir.statistics.services.data_providers.data_provider_exempted_members_that_work import (
    DataProviderExemptedMembersThatWork,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_is_working,
)


class TestDataProviderExemptedMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2022, month=7, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2021, month=9, day=15, hour=10)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberDidAShiftButIsNotExempted_notIncluded(self):
        tapir_user = create_member_that_is_working(self, self.REFERENCE_TIME)
        shift = ShiftFactory.create(
            start_time=self.REFERENCE_TIME - datetime.timedelta(days=1)
        )
        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.DONE, user=tapir_user, slot=shift.slots.first()
        )

        queryset = DataProviderExemptedMembersThatWork.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberDidAShiftAndIsExempted_included(self):
        tapir_user = create_member_that_is_working(self, self.REFERENCE_TIME)
        shift = ShiftFactory.create(
            start_time=self.REFERENCE_TIME - datetime.timedelta(days=1)
        )
        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.DONE, user=tapir_user, slot=shift.slots.first()
        )
        ShiftExemption.objects.create(
            shift_user_data=tapir_user.shift_user_data,
            start_date=self.REFERENCE_TIME - datetime.timedelta(days=1),
        )

        queryset = DataProviderExemptedMembersThatWork.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

    def test_getQueryset_memberDidAShiftAndIsExemptedButTheShiftIsTooFarAway_notIncluded(
        self,
    ):
        tapir_user = create_member_that_is_working(self, self.REFERENCE_TIME)
        shift = ShiftFactory.create(
            start_time=self.REFERENCE_TIME - datetime.timedelta(days=90)
        )
        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.DONE, user=tapir_user, slot=shift.slots.first()
        )
        ShiftExemption.objects.create(
            shift_user_data=tapir_user.shift_user_data,
            start_date=self.REFERENCE_TIME - datetime.timedelta(days=1),
        )

        queryset = DataProviderExemptedMembersThatWork.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

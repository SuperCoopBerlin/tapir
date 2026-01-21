from datetime import timedelta
from django.db import IntegrityError
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    RecurringShiftWatch,
    ShiftWatch,
    StaffingStatusChoices,
    Shift,
)
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.tests.factories import ShiftFactory, ShiftWatchFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftWatchCreationEdgeCases(TapirFactoryTestBase):

    def setUp(self):
        self.user = TapirUserFactory.create()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=8)
        self.base_shift = ShiftFactory.create(start_time=start, end_time=end)

        self.recurring_weekday = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[(timezone.now() + timedelta(days=1)).weekday()],
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )

    def test_createShiftWatchForShift_createDuplicateEntry_avoidedIfExisting(self):
        """Ensure no duplicate ShiftWatch for (user, shift) is created."""
        ShiftWatchFactory(user=self.user, shift=self.base_shift)

        ShiftWatchCreator.create_shift_watches_for_shift(self.base_shift)

        watches = ShiftWatch.objects.filter(user=self.user, shift=self.base_shift)
        self.assertEqual(watches.count(), 1)

    def test_createShiftWatchesForRecurring_existingShiftWatch_skipsExisting(self):
        """Skip existing ShiftWatches when creating for recurring shifts."""
        recurring = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[self.base_shift.start_time.weekday()],
            staffing_status=[StaffingStatusChoices.ALL_CLEAR],
        )

        ShiftWatchFactory(user=self.user, shift=self.base_shift)

        ShiftWatchCreator.create_shift_watches_for_recurring(recurring)

        self.assertEqual(ShiftWatch.objects.filter(shift=self.base_shift).count(), 1)

    def test_createShiftWatchForShift_shiftWithoutTemplate_getsAccepted(self):
        """Ensure no crash if shift.shift_template or group is None."""
        start = timezone.now() + timedelta(days=5)
        shift = Shift.objects.create(
            start_time=start,
            end_time=start + timedelta(hours=8),
            shift_template=None,
        )

        RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[shift.start_time.weekday()],
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )

        ShiftWatchCreator.create_shift_watches_for_shift(shift)

        self.assertTrue(ShiftWatch.objects.filter(shift=shift).exists())

    def test_createShiftWatchesForRecurring_RecurringWithoutCriteria_createsNoShiftwtch(
        self,
    ):
        """If recurring has no criteria set, no ShiftWatch should be created."""
        recurring_empty = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[],
            staffing_status=[StaffingStatusChoices.ALL_CLEAR],
        )

        # Create two shifts which should not be existing after
        start1 = timezone.now() + timedelta(days=6)
        start2 = timezone.now() + timedelta(days=7)
        ShiftFactory.create(start_time=start1, end_time=start1 + timedelta(hours=8))
        ShiftFactory.create(start_time=start2, end_time=start2 + timedelta(hours=8))

        ShiftWatchCreator.create_shift_watches_for_recurring(recurring_empty)

        self.assertEqual(
            ShiftWatch.objects.filter(recurring_template=recurring_empty).count(), 0
        )

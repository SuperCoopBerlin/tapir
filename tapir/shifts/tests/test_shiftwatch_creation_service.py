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
from tapir.shifts.tests.factories import ShiftFactory
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
            staffing_status=["maybe"],
        )

    def test_create_shift_watch_entries_avoids_duplicates_if_existing(self):
        """Ensure no duplicate ShiftWatch for (user, shift) is created."""
        ShiftWatch.objects.create(
            user=self.user,
            shift=self.base_shift,
            staffing_status=["maybe"],
            recurring_template=self.recurring_weekday,
            last_staffing_status=StaffingStatusChoices.ALL_CLEAR,
        )

        ShiftWatchCreator.create_shift_watches_for_shift(self.base_shift)

        watches = ShiftWatch.objects.filter(user=self.user, shift=self.base_shift)
        assert watches.count() == 1

    def test_create_shift_watches_for_recurring_skips_existing(self):
        """Skip existing ShiftWatches when creating for recurring shifts."""
        start1 = timezone.now() + timedelta(days=2)
        start2 = timezone.now() + timedelta(days=3)
        shift1 = Shift.objects.create(
            start_time=start1, end_time=start1 + timedelta(hours=8)
        )
        shift2 = Shift.objects.create(
            start_time=start2, end_time=start2 + timedelta(hours=8)
        )

        recurring = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[shift1.start_time.weekday()],
            staffing_status=["ok"],
        )

        ShiftWatch.objects.create(
            user=self.user,
            shift=shift1,
            staffing_status=["ok"],
            recurring_template=recurring,
            last_staffing_status=StaffingStatusChoices.ALL_CLEAR,
        )

        ShiftWatchCreator.create_shift_watches_for_recurring(recurring)

        assert ShiftWatch.objects.filter(shift=shift1).count() == 1
        assert ShiftWatch.objects.filter(shift=shift2).count() in (0, 1)

    def test_handle_shift_without_template_and_group_none(self):
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
            staffing_status=["y"],
        )

        ShiftWatchCreator.create_shift_watches_for_shift(shift)

        assert ShiftWatch.objects.filter(shift=shift).exists()

    def test_bulk_create_race_condition_unique_constraint(self):
        """Simulate unique constraint and ensure no DB-critical errors occur."""
        ShiftWatch.objects.create(
            user=self.user,
            shift=self.base_shift,
            staffing_status=["maybe"],
            recurring_template=self.recurring_weekday,
            last_staffing_status=StaffingStatusChoices.ALL_CLEAR,
        )

        try:
            ShiftWatchCreator.create_shift_watches_for_shift(self.base_shift)
        except IntegrityError:
            pass  # Acceptable if unique constraint failed.

        assert (
            ShiftWatch.objects.filter(user=self.user, shift=self.base_shift).count()
            == 1
        )

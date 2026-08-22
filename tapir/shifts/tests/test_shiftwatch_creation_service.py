import datetime
import time

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    RecurringShiftWatch,
    Shift,
    ShiftWatch,
    StaffingStatusChoices,
)
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.tests.factories import (
    ShiftFactory,
    ShiftTemplateFactory,
    ShiftWatchFactory,
)
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestShiftWatchCreationEdgeCases(TapirFactoryTestBase):

    def setUp(self):
        self.user = TapirUserFactory.create()
        mock_timezone_now(
            self,
            datetime.datetime(
                year=2026,
                month=3,
                day=16,
                hour=15,
                minute=0,
                second=0,
                tzinfo=datetime.UTC,
            ),
        )

        start = timezone.now() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(hours=8)
        self.base_shift = ShiftFactory.create(start_time=start, end_time=end)

    def test_createShiftWatchForShift_createDuplicateEntry_avoidedIfExisting(self):
        """Ensure no duplicate ShiftWatch for (user, shift) is created."""
        ShiftWatchFactory(user=self.user, shift=self.base_shift)

        ShiftWatchCreator.create_shift_watches_for_shift_based_on_recurring(
            self.base_shift
        )

        watches = ShiftWatch.objects.filter(user=self.user, shift=self.base_shift)
        self.assertEqual(watches.count(), 1)

    def test_createShiftWatchesForRecurring_existingShiftWatch_skipsExisting(self):
        """Skip existing ShiftWatches when creating for recurring shifts."""
        recurring = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[self.base_shift.start_time.weekday()],
            staffing_status=[StaffingStatusChoices.ALL_CLEAR],
            watched_capabilities=[],
        )

        ShiftWatchFactory(user=self.user, shift=self.base_shift)

        ShiftWatchCreator.create_shift_watches_for_recurring(recurring)

        self.assertEqual(ShiftWatch.objects.filter(shift=self.base_shift).count(), 1)

    def test_createShiftWatchForShift_shiftWithoutTemplate_getsAccepted(self):
        """Ensure no crash if shift.shift_template or group is None."""
        start = timezone.now() + datetime.timedelta(days=5)
        shift = Shift.objects.create(
            start_time=start,
            end_time=start + datetime.timedelta(hours=8),
            shift_template=None,
        )

        RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[shift.start_time.weekday()],
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
            watched_capabilities=[],
        )

        ShiftWatchCreator.create_shift_watches_for_shift_based_on_recurring(shift)

        self.assertTrue(ShiftWatch.objects.filter(shift=shift).exists())

    def test_createShiftWatchesForRecurring_RecurringWithoutCriteria_createsNoShiftwatch(
        self,
    ):
        """If recurring has no criteria set, no ShiftWatch should be created."""
        recurring_empty = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[],
            staffing_status=[StaffingStatusChoices.ALL_CLEAR],
            watched_capabilities=[],
        )

        # Create two shifts which should not be existing after
        start1 = timezone.now() + datetime.timedelta(days=6)
        start2 = timezone.now() + datetime.timedelta(days=7)
        ShiftFactory.create(
            start_time=start1, end_time=start1 + datetime.timedelta(hours=8)
        )
        ShiftFactory.create(
            start_time=start2, end_time=start2 + datetime.timedelta(hours=8)
        )

        ShiftWatchCreator.create_shift_watches_for_recurring(recurring_empty)

        self.assertEqual(
            ShiftWatch.objects.filter(recurring_template=recurring_empty).count(), 0
        )

    def test_createShiftfromShiftTemplate_intersectingRecurringShiftWatch_shiftWatchIsCreatedNoOverWrite(
        self,
    ):
        """Test to ensure correct ShiftWatch creation with intersecting recurring ShiftWatch."""
        monday = timezone.now() + datetime.timedelta(
            days=(7 - timezone.now().date().weekday() % 7)
        )

        shift_template_1 = ShiftTemplateFactory.create()
        shift_1 = shift_template_1.create_shift_if_necessary(start_date=monday.date())
        shift_3 = ShiftFactory.create(start_time=monday)

        recurring_template = RecurringShiftWatch.objects.create(user=self.user)
        recurring_template.shift_templates.set([shift_template_1])
        ShiftWatchCreator.create_shift_watches_for_recurring(
            recurring=recurring_template
        )

        recurring_template_2 = RecurringShiftWatch.objects.create(
            user=self.user, weekdays=[0]
        )
        ShiftWatchCreator.create_shift_watches_for_recurring(
            recurring=recurring_template_2
        )

        self.assertTrue(
            ShiftWatch.objects.filter(user=self.user, shift=shift_1).exists()
        )
        self.assertTrue(
            ShiftWatch.objects.filter(user=self.user, shift=shift_3).exists()
        )

        shift_watch_1 = ShiftWatch.objects.get(user=self.user, shift=shift_1)
        shift_watch_3 = ShiftWatch.objects.get(user=self.user, shift=shift_3)

        self.assertEqual(shift_watch_1.recurring_template, recurring_template)
        self.assertEqual(shift_watch_3.recurring_template, recurring_template_2)

    def test_createShiftWatchesForRecurring_benchmark_belowThresholds(self):

        recurring = RecurringShiftWatch.objects.create(
            user=self.user,
            weekdays=[0, 1, 2, 3, 4, 5, 6],
            staffing_status=[StaffingStatusChoices.ALL_CLEAR],
            watched_capabilities=[],
        )

        # Create 1500 shifts
        shifts = []
        base_date = timezone.now().date() + datetime.timedelta(days=1)

        for day_offset in range(150):
            current_date = base_date + datetime.timedelta(days=day_offset)
            for shift_num in range(10):
                start_time = timezone.make_aware(
                    datetime.datetime.combine(
                        current_date,
                        datetime.time(
                            hour=6 + (shift_num // 2), minute=30 * (shift_num % 2)
                        ),
                    )
                )
                end_time = start_time + datetime.timedelta(hours=2)
                shifts.append(Shift(start_time=start_time, end_time=end_time))

        Shift.objects.bulk_create(shifts, batch_size=500)

        with CaptureQueriesContext(connection) as ctx:
            start_time = time.time()
            ShiftWatchCreator.create_shift_watches_for_recurring(recurring)
            elapsed = time.time() - start_time

        query_count = len(ctx)
        watches_count = ShiftWatch.objects.filter(recurring_template=recurring).count()

        print(f"""
        --------------------------------------------------------
        Shifts Created:    {watches_count:<17}
        Time Elapsed:      {elapsed:.2f}s           
        Database Queries:  {query_count:<17}
        Queries/Shift:     {query_count / watches_count:.3f}   
        --------------------------------------------------------      
        """)

        self.assertEqual(watches_count, len(shifts) + 1)
        self.assertLess(elapsed, 3, f"Took {elapsed:.2f}s, expected < 3s")
        # Expected: ~10-15 queries
        self.assertLess(query_count, 15, f"{query_count} queries")

import datetime
from unittest.mock import Mock

from tapir.shifts.config import FEATURE_FLAG_AUTO_CANCEL_HOLIDAYS
from tapir.shifts.models import ShiftTemplateGroup, Shift
from tapir.shifts.services.shift_generator import ShiftGenerator
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, FeatureFlagTestMixin


class TestCreateShiftsForGroup(FeatureFlagTestMixin, TapirFactoryTestBase):
    def test_createShiftsForGroup_givenDateIsNotAMonday_raisesError(self):
        with self.assertRaises(ValueError):
            ShiftGenerator.create_shifts_for_group(
                at_date=datetime.date(2025, 11, 11),  # tuesday
                group=Mock(),
            )

    def test_createShiftsForGroup_noFilterGiven_createsShiftsForAllRelevantTemplates(
        self,
    ):
        group_a, group_b = ShiftTemplateGroup.objects.bulk_create(
            [ShiftTemplateGroup(name="A"), ShiftTemplateGroup(name="B")]
        )

        start_date_in_the_past = ShiftTemplateFactory.create(
            group=group_a, start_date=datetime.date(2020, 1, 1)
        )
        start_date_null = ShiftTemplateFactory.create(group=group_a, start_date=None)

        wrong_group = ShiftTemplateFactory.create(group=group_b, start_date=None)
        start_date_in_the_future = ShiftTemplateFactory.create(
            group=group_a, start_date=datetime.date(2025, 11, 12)
        )

        ShiftGenerator.create_shifts_for_group(
            at_date=datetime.date(2025, 11, 10),
            group=group_a,
        )

        self.assertEqual(1, start_date_in_the_past.generated_shifts.count())
        self.assertEqual(1, start_date_null.generated_shifts.count())
        self.assertEqual(0, wrong_group.generated_shifts.count())
        self.assertEqual(0, start_date_in_the_future.generated_shifts.count())

    def test_createShiftsForGroup_withFilter_createsShiftsForAllFilteredShifts(
        self,
    ):
        group_a, group_b = ShiftTemplateGroup.objects.bulk_create(
            [ShiftTemplateGroup(name="A"), ShiftTemplateGroup(name="B")]
        )

        template_1 = ShiftTemplateFactory.create(group=group_a)
        template_2 = ShiftTemplateFactory.create(group=group_a)
        template_3 = ShiftTemplateFactory.create(group=group_a)
        template_4 = ShiftTemplateFactory.create(group=group_b)

        ShiftGenerator.create_shifts_for_group(
            at_date=datetime.date(2025, 11, 10),
            group=group_a,
            filter_shift_template_ids={template_1.id, template_2.id, template_4.id},
        )

        self.assertEqual(1, template_1.generated_shifts.count())
        self.assertEqual(1, template_2.generated_shifts.count())
        self.assertEqual(0, template_3.generated_shifts.count())
        self.assertEqual(
            0,
            template_4.generated_shifts.count(),
            "Template 4 is included in the filter but is on the wrong group",
        )

    def test_createShiftsForGroup_withHolidayCancellation_cancelsHolidays(
        self,
    ):
        self.given_feature_flag_value(
            flag_name=FEATURE_FLAG_AUTO_CANCEL_HOLIDAYS, flag_value=True
        )
        group_a = ShiftTemplateGroup.objects.create(name="A")
        shift_template = ShiftTemplateFactory.create(group=group_a, weekday=3)

        ShiftGenerator.create_shifts_for_group(
            at_date=datetime.date(2025, 12, 29),
            group=group_a,
        )

        self.assertEqual(1, shift_template.generated_shifts.count())
        shift = Shift.objects.get()
        self.assertEqual(
            datetime.date(year=2026, month=1, day=1), shift.start_time.date()
        )
        self.assertTrue(shift.cancelled)
        self.assertEqual("Neujahr", shift.cancelled_reason)

    def test_createShiftsForGroup_withoutHolidayCancellation_doesntCancelsHolidays(
        self,
    ):
        self.given_feature_flag_value(
            flag_name=FEATURE_FLAG_AUTO_CANCEL_HOLIDAYS, flag_value=False
        )
        group_a = ShiftTemplateGroup.objects.create(name="A")
        shift_template = ShiftTemplateFactory.create(group=group_a, weekday=3)

        ShiftGenerator.create_shifts_for_group(
            at_date=datetime.date(2025, 12, 29),
            group=group_a,
        )

        self.assertEqual(1, shift_template.generated_shifts.count())
        shift = Shift.objects.get()
        self.assertEqual(
            datetime.date(year=2026, month=1, day=1), shift.start_time.date()
        )
        self.assertFalse(shift.cancelled)
        self.assertIsNone(shift.cancelled_reason)

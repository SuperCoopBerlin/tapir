import datetime
from unittest.mock import Mock

from tapir.shifts.models import ShiftTemplateGroup
from tapir.shifts.services.shift_generator import ShiftGenerator
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateShiftsForGroup(TapirFactoryTestBase):
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

    def test_createShiftsForGroup_with_createsShiftsForAllFilteredShifts(
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

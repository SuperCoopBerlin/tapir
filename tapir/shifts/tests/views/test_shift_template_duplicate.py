import datetime
from itertools import product
from unittest.mock import patch, Mock

from django.urls import reverse

from tapir.shifts.models import ShiftTemplate, ShiftTemplateGroup
from tapir.shifts.services.shift_generator import ShiftGenerator
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftTemplateDuplicate(TapirFactoryTestBase):
    def test_shiftTemplateDuplicateView_default_allFieldsGetsCopied(
        self,
    ):
        self.login_as_member_office_user()
        group_a, group_b = ShiftTemplateGroup.objects.bulk_create(
            [ShiftTemplateGroup(name="A"), ShiftTemplateGroup(name="B")]
        )
        shift_template_source = ShiftTemplateFactory.create(
            start_date=datetime.date.today() + datetime.timedelta(days=1),
            group=group_a,
            nb_slots=1,
            weekday=1,
        )

        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template_source.id]),
            {
                "week_group": [group_b.id],
                "weekdays": [3],
            },
            follow=True,
        )

        self.assertStatusCode(response, 200)
        self.assertEqual(2, ShiftTemplate.objects.count())

        shift_template_duplicate = ShiftTemplate.objects.get(group=group_b)
        self.assertEqual(shift_template_duplicate.name, shift_template_source.name)
        self.assertEqual(
            shift_template_duplicate.description, shift_template_source.description
        )
        self.assertEqual(shift_template_duplicate.group, group_b)
        self.assertEqual(
            shift_template_source.flexible_time, shift_template_duplicate.flexible_time
        )
        self.assertEqual(
            shift_template_source.num_required_attendances,
            shift_template_duplicate.num_required_attendances,
        )
        self.assertEqual(
            shift_template_source.start_date,
            shift_template_duplicate.start_date,
        )
        self.assertEqual(
            shift_template_source.start_time, shift_template_duplicate.start_time
        )
        self.assertEqual(
            shift_template_source.end_time,
            shift_template_duplicate.end_time,
        )
        self.assertEqual(
            shift_template_source.slot_templates.count(),
            shift_template_duplicate.slot_templates.count(),
        )
        self.assertEqual(
            shift_template_source.slot_templates.first().name,
            shift_template_duplicate.slot_templates.first().name,
        )

    def test_shiftTemplateDuplicateView_sourceTemplateIsIncludedInTheTargetInterval_dontDuplicateSourceOnSameGroupAndWeekday(
        self,
    ):
        self.login_as_member_office_user()
        group_a, group_b = ShiftTemplateGroup.objects.bulk_create(
            [ShiftTemplateGroup(name="A"), ShiftTemplateGroup(name="B")]
        )

        shift_template = ShiftTemplateFactory.create(
            start_date=datetime.datetime.now() + datetime.timedelta(days=1),
            group=group_a,
            weekday=1,
        )

        target_groups = [group_a.id, group_b.id]
        target_weekdays = [1, 2]
        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template.id]),
            {
                "week_group": target_groups,
                "weekdays": target_weekdays,
            },
            follow=True,
        )

        self.assertStatusCode(response, 200)
        self.assertEqual(
            4,
            ShiftTemplate.objects.count(),
            "There should be a new template for each combination except for group A day 1, since that is the source template",
        )

        for weekday, group_id in product(target_weekdays, target_groups):
            self.assertEqual(
                1,
                ShiftTemplate.objects.filter(
                    weekday=weekday, group_id=group_id
                ).count(),
            )

    @patch.object(ShiftGenerator, "generate_shifts_up_to", autospec=True)
    def test_shiftTemplateDuplicateView_default_generatesShiftsOnlyForTheNewTemplates(
        self, mock_generate_shifts_up_to: Mock
    ):
        self.login_as_member_office_user()
        group_a, group_b = ShiftTemplateGroup.objects.bulk_create(
            [ShiftTemplateGroup(name="A"), ShiftTemplateGroup(name="B")]
        )

        shift_template_source = ShiftTemplateFactory.create(
            start_date=datetime.datetime.now() + datetime.timedelta(days=1),
            group=group_a,
            weekday=1,
        )

        target_groups = [group_a.id, group_b.id]
        target_weekdays = [1, 2]
        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template_source.id]),
            {
                "week_group": target_groups,
                "weekdays": target_weekdays,
            },
            follow=True,
        )

        self.assertStatusCode(response, 200)
        self.assertEqual(
            4,
            ShiftTemplate.objects.count(),
        )

        mock_generate_shifts_up_to.assert_called_once_with(
            filter_group_ids={group_a.id, group_b.id},
            filter_shift_template_ids=set(
                ShiftTemplate.objects.exclude(id=shift_template_source.id).values_list(
                    "id", flat=True
                )
            ),
        )

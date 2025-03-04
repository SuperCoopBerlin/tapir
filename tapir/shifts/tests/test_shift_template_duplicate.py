from itertools import product

from django.urls import reverse
import datetime

from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.shifts.models import ShiftTemplate, ShiftTemplateGroup


class TestShiftTemplateDuplicate(TapirFactoryTestBase):
    def test_shiftTemplateDuplicateForm_duplicateSingleTemplate(self):
        self.login_as_member_office_user()
        ShiftTemplateGroup.objects.bulk_create(
            [
                ShiftTemplateGroup(name="A"),
                ShiftTemplateGroup(name="B"),
            ]
        )
        shift_template_source = ShiftTemplateFactory.create(
            start_date=datetime.date.today() + datetime.timedelta(days=1),
            group=ShiftTemplateGroup.objects.get(name="A"),
            weekday=1,
        )

        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template_source.pk]),
            {
                "start_date": shift_template_source.start_date,
                "start_time": shift_template_source.start_time,
                "end_time": shift_template_source.end_time,
                "week_group": 1,
                "weekdays": 3,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, ShiftTemplate.objects.count())
        shift_template_duplicate = ShiftTemplate.objects.all()[1]
        self.assertEqual(shift_template_duplicate.name, shift_template_source.name)
        self.assertEqual(
            shift_template_duplicate.description, shift_template_source.description
        )
        self.assertEqual(
            shift_template_source.flexible_time, shift_template_duplicate.flexible_time
        )
        self.assertEqual(
            shift_template_source.num_required_attendances,
            shift_template_source.num_required_attendances,
        )
        self.assertEqual(
            shift_template_duplicate.start_date,
            shift_template_source.start_date,
        )
        self.assertEqual(
            shift_template_duplicate.start_time, shift_template_source.start_time
        )
        self.assertEqual(
            shift_template_duplicate.end_time, shift_template_source.end_time
        )
        for duplicate_template, source_template in product(
            shift_template_duplicate.slot_templates.all(),
            shift_template_source.slot_templates.all(),
        ):
            self.assertEqual(duplicate_template.name, source_template.name)
            self.assertEqual(
                duplicate_template.required_capabilities,
                source_template.required_capabilities,
            )

    def test_shiftTemplateDuplicateForm_originalTemplateNotDuplicated(self):
        self.login_as_member_office_user()
        ShiftTemplateGroup.objects.bulk_create(
            [
                ShiftTemplateGroup(name="A"),
                ShiftTemplateGroup(name="B"),
            ]
        )
        shift_template = ShiftTemplateFactory.create(
            start_date=datetime.datetime.now() + datetime.timedelta(days=1),
            group=ShiftTemplateGroup.objects.get(name="A"),
            weekday=1,
        )

        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template.pk]),
            {
                "start_date": shift_template.start_date,
                "start_time": shift_template.start_time,
                "end_time": shift_template.end_time,
                "week_group": 0,
                "weekdays": 3,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, ShiftTemplate.objects.count())
        for template in ShiftTemplate.objects.all():
            self.assertEqual(template.slot_templates.name, None)

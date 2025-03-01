from django.urls import reverse
import datetime

from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.shifts.models import ShiftTemplate, ShiftTemplateGroup


class TestShiftTemplateDuplicate(TapirFactoryTestBase):
    def test_duplicate_shift_template(self):
        self.login_as_member_office_user()
        ShiftTemplateGroup.objects.bulk_create(
            [
                ShiftTemplateGroup(name="A"),
                ShiftTemplateGroup(name="B"),
                ShiftTemplateGroup(name="C"),
                ShiftTemplateGroup(name="D"),
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
                "week_group": [
                    1,
                    2,
                    3,
                ],
                "weekdays": [
                    1,
                    2,
                    3,
                ],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShiftTemplate.objects.count(), 9)
        for template in ShiftTemplate.objects.all():
            self.assertEqual(
                template.slot_templates.name, shift_template.slot_templates.name
            )

    def test_shiftTemplateDuplicateForm_duplicateSingleTemplate(self):
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
                "week_group": 1,
                "weekdays": 3,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShiftTemplate.objects.count(), 2)
        for template in ShiftTemplate.objects.all():
            self.assertEqual(
                template.slot_templates.name, shift_template.slot_templates.name
            )

    def test_shiftTemplateDuplicateForm_originalTemplateNotDuplcated(self):
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
        self.assertNotEqual(ShiftTemplate.objects.count(), 2)
        for template in ShiftTemplate.objects.all():
            self.assertEqual(template.slot_templates.name, None)

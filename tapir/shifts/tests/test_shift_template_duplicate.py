from itertools import product

from django.urls import reverse
import datetime

from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.shifts.models import ShiftTemplate, ShiftTemplateGroup


class TestShiftTemplateDuplicate(TapirFactoryTestBase):
    def test_shiftTemplateDuplicateView_duplicateSingleTemplate_allFieldsGetsCopied(
        self,
    ):
        self.login_as_member_office_user()
        ShiftTemplateGroup.objects.bulk_create(
            [ShiftTemplateGroup(name="A"), ShiftTemplateGroup(name="B")]
        )
        shift_template_source = ShiftTemplateFactory.create(
            start_date=datetime.date.today() + datetime.timedelta(days=1),
            group=ShiftTemplateGroup.objects.get(name="A"),
            weekday=1,
        )

        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template_source.id]),
            {
                "week_group": 1,
                "weekdays": 3,
            },
            follow=True,
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(2, ShiftTemplate.objects.count())
        shift_template_duplicate = ShiftTemplate.objects.exclude(
            id=shift_template_source.id
        ).get()
        self.assertEqual(shift_template_duplicate.name, shift_template_source.name)
        self.assertEqual(
            shift_template_duplicate.description, shift_template_source.description
        )
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
        for slot_template_source, slot_template_duplicate in product(
            shift_template_source.slot_templates.all(),
            shift_template_duplicate.slot_templates.all(),
        ):
            self.assertEqual(
                slot_template_source.name,
                slot_template_duplicate.name,
            )

    def test_shiftTemplateDuplicateView_duplicateSingleTemplate_originalTemplateGetsNotDuplicated(
        self,
    ):
        self.login_as_member_office_user()
        ShiftTemplateGroup.objects.create(name="A")
        shift_template = ShiftTemplateFactory.create(
            start_date=datetime.datetime.now() + datetime.timedelta(days=1),
            group=ShiftTemplateGroup.objects.get(name="A"),
            weekday=1,
        )

        response = self.client.post(
            reverse("shifts:shift_template_duplicate", args=[shift_template.id]),
            {
                "week_group": 0,
                "weekdays": 3,
            },
            follow=True,
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(1, ShiftTemplate.objects.count())

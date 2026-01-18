import datetime

import pytest
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftTemplateGroup, RecurringShiftWatch, ShiftWatch
from tapir.shifts.services.shift_generator import ShiftGenerator
from tapir.shifts.tests.factories import ShiftTemplateFactory


def future_date():
    return timezone.now().date() + datetime.timedelta(days=30)


@pytest.mark.django_db
class TestShiftRecurringTemplate:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = TapirUserFactory.create()
        self.recurring_template = RecurringShiftWatch.objects.create(user=self.user)

    @pytest.mark.parametrize(
        "recurring_weekdays, recurring_groups, recurring_templates, expected",
        [
            ([0], ["A"], [], {"template1"}),
            ([0], ["A", "B"], [], {"template1", "template3"}),
            ([0, 1], ["A"], [], {"template1", "template2"}),
            ([0, 1], ["A", "B"], [], {"template1", "template2", "template3"}),
        ],
    )
    def test_create_shift_from_shift_template_watch_a_monday_dont_create_other(
        self,
        recurring_weekdays,
        recurring_groups,
        recurring_templates,
        expected,
    ):
        a = ShiftTemplateGroup.objects.create(name="A")
        b = ShiftTemplateGroup.objects.create(name="B")
        template1 = ShiftTemplateFactory.create(group=a, weekday=0, name="template1")
        template2 = ShiftTemplateFactory.create(group=a, weekday=1, name="template2")
        template3 = ShiftTemplateFactory.create(group=b, weekday=0, name="template3")

        self.recurring_template.weekdays = recurring_weekdays
        self.recurring_template.shift_template_group = recurring_groups
        self.recurring_template.shift_templates.set(recurring_templates)
        self.recurring_template.save()

        ShiftGenerator.generate_shifts_up_to(end_date=future_date())

        print(ShiftWatch.objects.values_list("shift__shift_template__id", flat=True))
        print(
            "template1.id, template2.id, template3.id:",
            template1.name,
            template2.pk,
            template3.pk,
        )
        actual = set(
            ShiftWatch.objects.values_list(
                "shift__shift_template__name",
                flat=True,
            )
        )
        assert actual == expected

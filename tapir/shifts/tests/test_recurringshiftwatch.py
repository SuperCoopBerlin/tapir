import datetime
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    RecurringShiftWatch,
    ShiftWatch,
    ShiftTemplateGroup,
)
from tapir.shifts.services.shift_generator import ShiftGenerator
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


def make_group_with_templates(n=1, name="A"):
    group = ShiftTemplateGroup.objects.create(name=name)
    templates = [ShiftTemplateFactory.create(group=group) for _ in range(n)]
    return group, templates


def future_date(days=14):
    return timezone.now().date() + datetime.timedelta(days=days)


class ShiftRecurringTemplateTests(TapirFactoryTestBase):

    def setUp(self):
        self.user = TapirUserFactory.create()
        self.recurring_template = RecurringShiftWatch.objects.create(
            user=self.user,
        )

    def watched_template_ids(self):
        return set(
            ShiftWatch.objects.filter(user=self.user).values_list(
                "shift__shift_template", flat=True
            )
        )

    def watched_group_names(self):
        return set(
            ShiftWatch.objects.filter(user=self.user).values_list(
                "shift__shift_template__group__name", flat=True
            )
        )

    def test_createShiftBasedOnShiftTemplate_watchSingleShiftTemplates_shiftWatchIsCreated(
        self,
    ):
        _, [shift_template] = make_group_with_templates(1)
        self.recurring_template.shift_templates.set([shift_template])
        ShiftGenerator.generate_shifts_up_to(end_date=future_date())
        watched_shift_templates = self.watched_template_ids()

        self.assertEqual(watched_shift_templates, {shift_template.id})

    def test_createShiftBasedOnShiftTemplate_watchMultipleShiftTemplates_shiftWatchIsCreated(
        self,
    ):
        _, (shift_template_1, shift_template_2) = make_group_with_templates(2)
        self.recurring_template.shift_templates.set(
            [shift_template_1, shift_template_2]
        )
        end_date = future_date()
        ShiftGenerator.generate_shifts_up_to(end_date=end_date)
        watched_template_ids = self.watched_template_ids()
        expected_ids = {shift_template_1.id, shift_template_2.id}

        self.assertEqual(watched_template_ids, expected_ids)

    def test_createShiftOfOtherTemplate_watchMultipleShiftTemplates_shiftWatchIsNotCreated(
        self,
    ):
        _, (shift_template_1, shift_template_2, shift_template_3) = (
            make_group_with_templates(3)
        )
        self.recurring_template.shift_templates.set(
            [shift_template_1, shift_template_2]
        )
        end_date = future_date()
        ShiftGenerator.generate_shifts_up_to(end_date=end_date)
        watched_template_ids = self.watched_template_ids()
        expected_ids = {shift_template_1.id, shift_template_2.id}

        self.assertNotIn(shift_template_3.id, watched_template_ids)
        self.assertEqual(watched_template_ids, expected_ids)

    def test_createShiftfromShiftTemplate_watchABCD_shiftWatchIsCreated(self):
        group, _ = make_group_with_templates(1)
        self.recurring_template.shift_template_group = [group.name]
        self.recurring_template.save()
        end_date = future_date()
        ShiftGenerator.generate_shifts_up_to(end_date=end_date)
        watched_group_names = self.watched_group_names()

        self.assertEqual(watched_group_names, {group.name})

    def test_createShiftfromShiftTemplate_intersectingRecurringShiftWatch_shiftWatchIsCreatedNoOverWrite(
        self,
    ):

        monday = timezone.now() + datetime.timedelta(
            days=(7 - timezone.now().date().weekday() % 7)
        )

        shift_template_1 = ShiftTemplateFactory.create()
        shift_1 = shift_template_1.create_shift(start_date=monday.date())
        shift_3 = ShiftFactory.create(start_time=monday)

        # set both RecurringShiftWatch
        self.recurring_template.shift_templates.set([shift_template_1])

        ShiftWatchCreator.create_shift_watches_for_recurring(
            recurring=self.recurring_template
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

        self.assertEqual(shift_watch_1.recurring_template, self.recurring_template)
        self.assertEqual(shift_watch_3.recurring_template, recurring_template_2)

import datetime
from django.utils import timezone
import pytest
from django.utils.timezone import make_aware

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftRecurringWatchTemplate,
    ShiftWatch,
    Shift,
    ShiftTemplateGroup,
)
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class ShiftRecurringTemplateTests(TapirFactoryTestBase):

    def setUp(self):
        self.user = TapirUserFactory.create()
        self.recurring_template = ShiftRecurringWatchTemplate.objects.create(
            user=self.user,
        )

    def test_createShiftBasedOnShiftTemplate_watchSingleShiftTemplates_shiftWatchIsCreated(
        self,
    ):
        shift_template = ShiftTemplateFactory.create()
        self.recurring_template.shift_templates.set([shift_template])
        self.recurring_template.save()

        shift = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )

        self.assertTrue(ShiftWatch.objects.filter(user=self.user, shift=shift).exists())

    def test_createShiftBasedOnShiftTemplate_watchMultipleShiftTemplates_shiftWatchIsCreated(
        self,
    ):
        shift_template_1 = ShiftTemplateFactory.create()
        shift_template_2 = ShiftTemplateFactory.create()
        self.recurring_template.shift_templates.set(
            [shift_template_1, shift_template_2]
        )
        self.recurring_template.save()

        shift = shift_template_2.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )

        self.assertTrue(ShiftWatch.objects.filter(user=self.user, shift=shift).exists())

    def test_createShiftOfOtherTemplate_watchMultipleShiftTemplates_shiftWatchIsNotCreated(
        self,
    ):
        shift_template_1 = ShiftTemplateFactory.create()
        shift_template_2 = ShiftTemplateFactory.create()
        shift_template_3 = ShiftTemplateFactory.create()
        self.recurring_template.shift_templates.set(
            [shift_template_1, shift_template_2]
        )
        self.recurring_template.save()

        shift = shift_template_3.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )

        self.assertFalse(
            ShiftWatch.objects.filter(user=self.user, shift=shift).exists()
        )

    @pytest.mark.skip(reason="Should work in the future though")
    def test_createNonShiftTemplateShift_watch_shiftWatchIsCreated(self):
        self.recurring_template.weekdays = [6]
        self.recurring_template.save()
        shift = ShiftFactory.create(
            nb_slots=0,
            start_time=make_aware(
                datetime.datetime(year=2025, month=11, day=9)  # sunday
            ),
        )
        self.assertTrue(ShiftWatch.objects.filter(user=self.user, shift=shift).exists())

    def test_createShiftfromShiftTemplate_watchABCD_shiftWatchIsCreated(self):
        ShiftTemplateGroup.objects.create(name="A")
        group = ShiftTemplateGroup.objects.get(name="A")
        shift_template = ShiftTemplateFactory.create(group=group)
        self.recurring_template.shift_template_group = ["A"]
        self.recurring_template.save()

        shift = shift_template.create_shift(timezone.now().date())
        print(Shift.objects.all())
        self.assertTrue(ShiftWatch.objects.filter(user=self.user, shift=shift).exists())

    def test_createShiftfromShiftTemplate_intersectingShiftRecurringWatchTemplate_shiftWatchIsCreatedNoOverWrite(
        self,
    ):

        monday = timezone.now() + datetime.timedelta(
            days=(7 - timezone.now().date().weekday() % 7)
        )

        shift_template_1 = ShiftTemplateFactory.create()
        shift_1 = shift_template_1.create_shift(start_date=monday.date())
        shift_3 = ShiftFactory.create(start_time=monday)

        # set both ShiftRecurringWatchTemplate
        self.recurring_template.shift_templates.set([shift_template_1])
        self.recurring_template.save()
        self.recurring_template.create_shift_watches()
        recurring_template_2 = ShiftRecurringWatchTemplate.objects.create(
            user=self.user,
        )
        recurring_template_2.weekdays = [0]
        recurring_template_2.save()
        recurring_template_2.create_shift_watches()

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

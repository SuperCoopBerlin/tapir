from django.urls import reverse
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftRecurringWatchTemplate, StaffingStatusChoices
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateWatchRecurringShiftsView(TapirFactoryTestBase):
    VIEW_NAME = "shifts:create_watch_recurring_shifts"

    def test_createShiftRecurringWatchTemplate_weekdayAndShifTemplateGroup_entryCreated(
        self,
    ):
        tapir_user = self.login_as_normal_user()

        form_data = {
            "shift_templates": [],
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
            "staffing_status": [StaffingStatusChoices.UNDERSTAFFED],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 1)
        created_template = ShiftRecurringWatchTemplate.objects.first()

        self.assertEqual(set(created_template.weekdays), {1, 2})
        self.assertEqual(set(created_template.shift_template_group), {"A"})
        self.assertEqual(
            set(created_template.staffing_status), {StaffingStatusChoices.UNDERSTAFFED}
        )

    def test_createShiftRecurringWatchTemplate_ShiftTemplate_entryCreated(
        self,
    ):
        tapir_user = self.login_as_normal_user()

        a = ShiftTemplateFactory(name="Template 1")
        b = ShiftTemplateFactory(name="Template 2")

        form_data = {
            "shift_templates": [1, 2],
            "weekdays": [],
            "shift_template_group": [],
            "staffing_status": [StaffingStatusChoices.UNDERSTAFFED],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 1)
        created_template = ShiftRecurringWatchTemplate.objects.first()

        self.assertEqual(
            set(created_template.shift_templates.values_list("id", flat=True)), {1, 2}
        )
        self.assertEqual(
            set(created_template.staffing_status), {StaffingStatusChoices.UNDERSTAFFED}
        )

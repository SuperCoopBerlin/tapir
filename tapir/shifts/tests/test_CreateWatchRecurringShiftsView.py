from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftRecurringWatchTemplate, StaffingStatusChoices
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateWatchRecurringShiftsView(TapirFactoryTestBase):
    VIEW_NAME = "shifts:create_watch_recurring_shifts"

    def setUp(self):
        super().setUp()
        self.tapir_user = self.login_as_normal_user()

        self.template1 = ShiftTemplateFactory(name="Template 1")
        self.template2 = ShiftTemplateFactory(name="Template 2")

        self.default_form_data = {
            "shift_templates": [],
            "weekdays": [],
            "shift_template_group": [],
            "staffing_status": [StaffingStatusChoices.UNDERSTAFFED],
        }

    def test_createShiftRecurringWatchTemplate_weekdayAndShifTemplateGroup_entryCreated(
        self,
    ):
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 1)
        created_template = ShiftRecurringWatchTemplate.objects.first()

        self.assertEqual(set(created_template.weekdays), {1, 2})
        self.assertEqual(set(created_template.shift_template_group), {"A"})
        self.assertEqual(
            set(created_template.staffing_status), {StaffingStatusChoices.UNDERSTAFFED}
        )

    def test_createShiftRecurringWatchTemplate_ShiftTemplate_entryCreated(self):
        form_data = {
            **self.default_form_data,
            "shift_templates": [self.template1.id, self.template2.id],  # Use actual IDs
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 1)
        created_template = ShiftRecurringWatchTemplate.objects.first()

        self.assertEqual(
            set(created_template.shift_templates.values_list("id", flat=True)),
            {self.template1.id, self.template2.id},
        )
        self.assertEqual(
            set(created_template.staffing_status), {StaffingStatusChoices.UNDERSTAFFED}
        )

    def test_createShiftRecurringWatchTemplate_ShiftTemplateandWeekdayAndShiftTemplateGroup_validationError(
        self,
    ):
        form_data = {
            "shift_templates": [self.template1.id, self.template2.id],
            "weekdays": [1, 2],
            "shift_template_group": [],
        }
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]),
            data=form_data,
        )
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 0)
        self.assertFormError(
            response.context["form"],
            None,
            "If weekdays or shift_template_group are selected, ShiftTemplates may not be selected, and vice versa.",
        )

    #
    def test_createShiftRecurringWatchTemplate_nothingSelected_validationError(self):
        form_data = self.default_form_data
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]),
            data=form_data,
        )

        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 0)
        self.assertFormError(
            response.context["form"],
            None,
            "At least one of the fields (ShiftTemplates, weekdays, or shift_template_group) must be selected.",
        )

    def test_normal_user_cannot_update_other_(self):
        target: TapirUser = TapirUserFactory.create()
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[target.pk]), data=form_data
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 0)

    def test_member_office_user_can_update_other_username(self):
        self.login_as_member_office_user()
        target: TapirUser = TapirUserFactory.create()
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[target.pk]), data=form_data
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 1)

from django.urls import reverse
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
        self.assertFormError(
            response.context["form"],
            None,
            "If weekdays or shift_template_group are selected, ShiftTemplates may not be selected.",
        )

    #
    # # def test_clean_no_selection_raises_validation_error(self):
    # #     # Create a user for testing
    # #     tapir_user = TapirUserFactory.create()
    # #
    # #     form_data = {
    # #         "shift_templates": [],  # No templates selected
    # #         "weekdays": [],  # No weekdays selected
    # #         "shift_template_group": [],  # No group selected
    # #         "staffing_status": [StaffingStatusChoices.UNDERSTAFFED],  # Empty statuses
    # #     }
    # #
    # #     response = self.client.post(
    # #         reverse("shifts:create_watch_recurring_shifts", args=[tapir_user.id]),
    # #         data=form_data,
    # #     )
    # #     print(response.context["form"])
    # #     # Check that the response is valid but the form contains errors
    # #     # self.assertEqual(response.status_code, 200)  # Should return to form page
    # #     self.assertEqual(ShiftRecurringWatchTemplate.objects.count(), 0)
    # #     self.assertFormError(
    # #         response,
    # #         "form",
    # #         None,
    # #         "At least one of the fields (ShiftTemplates, weekdays, or shift_template_group) must be selected.",
    # #     )

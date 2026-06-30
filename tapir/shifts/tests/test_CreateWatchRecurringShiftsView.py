from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.forms import RecurringShiftWatchForm
from tapir.shifts.models import (
    RecurringShiftWatch,
    ShiftUserCapability,
    StaffingStatusChoices,
)
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

    def test_createRecurringShiftWatch_weekdayAndShifTemplateGroup_entryCreated(
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
        self.assertEqual(RecurringShiftWatch.objects.count(), 1)
        created_template = RecurringShiftWatch.objects.first()

        self.assertEqual(set(created_template.weekdays), {1, 2})
        self.assertEqual(set(created_template.shift_template_group), {"A"})
        self.assertEqual(
            set(created_template.staffing_status), {StaffingStatusChoices.UNDERSTAFFED}
        )

    def test_createRecurringShiftWatch_ShiftTemplate_entryCreated(self):
        form_data = {
            **self.default_form_data,
            "shift_templates": [self.template1.id, self.template2.id],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RecurringShiftWatch.objects.count(), 1)
        created_template = RecurringShiftWatch.objects.first()

        self.assertEqual(
            set(created_template.shift_templates.values_list("id", flat=True)),
            {self.template1.id, self.template2.id},
        )
        self.assertEqual(
            set(created_template.staffing_status), {StaffingStatusChoices.UNDERSTAFFED}
        )

    def test_createRecurringShiftWatch_ShiftTemplateandWeekdayAndShiftTemplateGroup_validationError(
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

        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_createRecurringShiftWatch_nothingSelected_validationError(self):
        form_data = self.default_form_data
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]),
            data=form_data,
        )

        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_createRecurringShiftWatch_normalUserAttemptsToCreateForOthers_403Error(
        self,
    ):
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
        self.assertEqual(RecurringShiftWatch.objects.count(), 0)

    def test_createRecurringShiftWatch_memberOfficeAttemptsToCreateForOthers_entryCreated(
        self,
    ):
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
        self.assertEqual(RecurringShiftWatch.objects.count(), 1)

    def test_createRecurringShiftWatch_withWatchedCapabilities_entrySaved(self):
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
            "watched_capabilities": [
                ShiftUserCapability.CASHIER,
                ShiftUserCapability.BREAD_DELIVERY,
            ],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RecurringShiftWatch.objects.count(), 1)
        created_watch = RecurringShiftWatch.objects.first()

        self.assertEqual(
            set(created_watch.watched_capabilities),
            {ShiftUserCapability.CASHIER, ShiftUserCapability.BREAD_DELIVERY},
        )

    def test_createRecurringShiftWatch_noCapabilitiesSelected_entryCreated(self):
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
            "watched_capabilities": [],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        created_watch = RecurringShiftWatch.objects.first()
        self.assertEqual(created_watch.watched_capabilities, [])

    def test_createRecurringShiftWatch_invalidCapability_validationError(self):
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
            "watched_capabilities": ["invalid_capability"],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("watched_capabilities", form.errors)

    def test_createRecurringShiftWatch_withCapabilitiesAndStaffingStatus_entrySaved(
        self,
    ):
        form_data = {
            **self.default_form_data,
            "weekdays": [1, 2],
            "shift_template_group": ["A"],
            "staffing_status": [
                StaffingStatusChoices.UNDERSTAFFED,
                StaffingStatusChoices.FULL,
            ],
            "watched_capabilities": [
                ShiftUserCapability.CASHIER,
                ShiftUserCapability.BREAD_DELIVERY,
            ],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RecurringShiftWatch.objects.count(), 1)
        created_watch = RecurringShiftWatch.objects.first()

        self.assertEqual(
            set(created_watch.staffing_status),
            {StaffingStatusChoices.UNDERSTAFFED, StaffingStatusChoices.FULL},
        )
        self.assertEqual(
            set(created_watch.watched_capabilities),
            {ShiftUserCapability.CASHIER, ShiftUserCapability.BREAD_DELIVERY},
        )

    def test_createRecurringShiftWatch_neitherStaffingStatusNorCapabilities_validationError(
        self,
    ):
        form_data = {
            "shift_templates": [],
            "weekdays": [1, 2],
            "shift_template_group": [],
            "staffing_status": [],
            "watched_capabilities": [],
        }

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[self.tapir_user.pk]), data=form_data
        )

        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn(
            RecurringShiftWatchForm.AT_LEAST_ONE_TARGET_ERROR,
            form.non_field_errors(),
        )

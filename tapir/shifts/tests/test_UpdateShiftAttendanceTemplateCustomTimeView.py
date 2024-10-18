import datetime

from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendanceTemplate, ShiftTemplate
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestUpdateShiftAttendanceTemplateCustomTimeView(TapirFactoryTestBase):
    CUSTOM_TIME_BEFORE = datetime.time(hour=8, minute=30)
    CUSTOM_TIME_AFTER = datetime.time(hour=12, minute=30)

    def create_attendance_template_for_user(self, tapir_user):
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(flexible_time=True)
        return ShiftAttendanceTemplate.objects.create(
            user=tapir_user,
            slot_template=shift_template.slot_templates.first(),
            custom_time=self.CUSTOM_TIME_BEFORE,
        )

    def try_to_update_custom_time(self, attendance_template) -> TemplateResponse:
        return self.client.post(
            reverse(
                "shifts:attendance_template_custom_time", args=[attendance_template.id]
            ),
            data={"custom_time": self.CUSTOM_TIME_AFTER},
        )

    def assertSuccess(self, response, attendance_template):
        self.assertRedirects(
            response,
            reverse(
                "shifts:shift_template_detail",
                args=[attendance_template.slot_template.shift_template.id],
            ),
        )
        attendance_template.refresh_from_db()
        self.assertEqual(attendance_template.custom_time, self.CUSTOM_TIME_AFTER)

    def assertAccessForbidden(self, response, attendance_template):
        self.assertEqual(403, response.status_code)
        attendance_template.refresh_from_db()
        self.assertEqual(attendance_template.custom_time, self.CUSTOM_TIME_BEFORE)

    def test_updateShiftAttendanceTemplateCustomTimeView_normalUserUpdatesOwnTime_success(
        self,
    ):
        tapir_user = self.login_as_normal_user()
        attendance_template = self.create_attendance_template_for_user(tapir_user)

        response = self.try_to_update_custom_time(attendance_template)

        self.assertSuccess(response, attendance_template)

    def test_updateShiftAttendanceTemplateCustomTimeView_normalUserUpdatesTimeOfOtherUser_accessForbidden(
        self,
    ):
        self.login_as_normal_user()
        registered_user = TapirUserFactory.create()
        attendance_template = self.create_attendance_template_for_user(registered_user)

        response = self.try_to_update_custom_time(attendance_template)

        self.assertAccessForbidden(response, attendance_template)

    def test_updateShiftAttendanceTemplateCustomTimeView_memberOfficeUpdatesTimeOfOtherUser_success(
        self,
    ):
        self.login_as_member_office_user()
        registered_user = TapirUserFactory.create()
        attendance_template = self.create_attendance_template_for_user(registered_user)

        response = self.try_to_update_custom_time(attendance_template)

        self.assertSuccess(response, attendance_template)

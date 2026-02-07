import datetime

from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendance
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestUpdateShiftAttendanceCustomTimeView(TapirFactoryTestBase):
    CUSTOM_TIME_BEFORE = datetime.time(hour=8, minute=30)
    CUSTOM_TIME_AFTER = datetime.time(hour=12, minute=30)

    def create_attendance_for_user(self, tapir_user):
        start_time = datetime.datetime(
            year=2024, month=6, day=15, hour=7, tzinfo=datetime.timezone.utc
        )
        shift = ShiftFactory.create(
            flexible_time=True,
            start_time=start_time,
            end_time=start_time.replace(hour=22),
        )
        return ShiftAttendance.objects.create(
            user=tapir_user,
            slot=shift.slots.first(),
            custom_time=self.CUSTOM_TIME_BEFORE,
        )

    def try_to_update_custom_time(self, attendance) -> TemplateResponse:
        return self.client.post(
            reverse("shifts:attendance_custom_time", args=[attendance.id]),
            data={"custom_time": self.CUSTOM_TIME_AFTER},
        )

    def assertSuccess(self, response, attendance):
        self.assertRedirects(
            response, reverse("shifts:shift_detail", args=[attendance.slot.shift.id])
        )
        attendance.refresh_from_db()
        self.assertEqual(attendance.custom_time, self.CUSTOM_TIME_AFTER)

    def assertAccessForbidden(self, response, attendance):
        self.assertEqual(403, response.status_code)
        attendance.refresh_from_db()
        self.assertEqual(attendance.custom_time, self.CUSTOM_TIME_BEFORE)

    def test_updateShiftAttendanceCustomTimeView_normalUserUpdatesOwnTime_success(self):
        tapir_user = self.login_as_normal_user()
        attendance = self.create_attendance_for_user(tapir_user)

        response = self.try_to_update_custom_time(attendance)

        self.assertSuccess(response, attendance)

    def test_updateShiftAttendanceCustomTimeView_normalUserUpdatesTimeOfOtherUser_accessForbidden(
        self,
    ):
        self.login_as_normal_user()
        registered_user = TapirUserFactory.create()
        attendance = self.create_attendance_for_user(registered_user)

        response = self.try_to_update_custom_time(attendance)

        self.assertAccessForbidden(response, attendance)

    def test_updateShiftAttendanceCustomTimeView_memberOfficeUpdatesTimeOfOtherUser_success(
        self,
    ):
        self.login_as_member_office_user()
        registered_user = TapirUserFactory.create()
        attendance = self.create_attendance_for_user(registered_user)

        response = self.try_to_update_custom_time(attendance)

        self.assertSuccess(response, attendance)

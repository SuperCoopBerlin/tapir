from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import strip_tags

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendanceMode, UpdateShiftUserDataLogEntry
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestEditShiftUserDataView(TapirFactoryTestBase):
    VIEW_NAME = "shifts:edit_shift_user_data"

    def test_editShiftUserDataView_loggedInAsNormalUser_notAuthorized(self):
        tapir_user = self.login_as_normal_user()

        response = self.client.get(
            reverse(self.VIEW_NAME, args=[tapir_user.shift_user_data.id])
        )

        self.assertEqual(403, response.status_code)

    def test_editShiftUserDataView_default_contextDataIsCorrect(self):
        self.login_as_member_office_user(preferred_language="en")

        tapir_user = TapirUserFactory.create(
            first_name="Hyper", usage_name="Super", last_name="Coop"
        )
        response: TemplateResponse = self.client.get(
            reverse(self.VIEW_NAME, args=[tapir_user.shift_user_data.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            f"Edit user shift data: Super Coop #{tapir_user.get_member_number()}",
            response.context_data["page_title"],
        )
        self.assertEqual(
            f"Edit user shift data: Super Coop #{tapir_user.get_member_number()}",
            strip_tags(response.context_data["card_title"]),
        )

    def test_editShiftUserDataView_default_createsLogEntry(self):
        self.login_as_member_office_user()
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        tapir_user.shift_user_data.save()

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.shift_user_data.id]),
            data={"attendance_mode": ShiftAttendanceMode.REGULAR},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        tapir_user.shift_user_data.refresh_from_db()
        self.assertEqual(
            tapir_user.shift_user_data.attendance_mode, ShiftAttendanceMode.REGULAR
        )
        self.assertEqual(1, UpdateShiftUserDataLogEntry.objects.count())

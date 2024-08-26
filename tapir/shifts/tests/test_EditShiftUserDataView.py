import datetime

from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import strip_tags

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
    ShiftTemplate,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
    ShiftSlot,
    ShiftAttendance,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


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

    def test_editShiftUserDataView_changingToFlyingAndUserHasAbcdAttendance_requiresConfirmation(
        self,
    ):
        self.login_as_member_office_user()

        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        tapir_user.shift_user_data.save()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=1)
        slot_template: ShiftSlotTemplate = shift_template.slot_templates.first()
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=slot_template
        )

        url = reverse(self.VIEW_NAME, args=[tapir_user.shift_user_data.id])
        response = self.client.post(
            url,
            data={"attendance_mode": ShiftAttendanceMode.FLYING},
        )
        self.assertEqual(200, response.status_code)

        self.assertIn(
            "confirm_delete_abcd_attendance",
            response.content.decode(),
            "There should be a warning about the member being registered to an ABCD shift .",
        )
        self.assertEqual(
            1,
            ShiftAttendanceTemplate.objects.count(),
            "The abcd attendance should not have been deleted.",
        )
        tapir_user.shift_user_data.refresh_from_db()
        self.assertEqual(
            ShiftAttendanceMode.REGULAR,
            tapir_user.shift_user_data.attendance_mode,
            "The user's attendance should not have been updated.",
        )

    def test_editShiftUserDataView_changingToFlyingAndUserDoesntHaveAbcdAttendance_noConfirmation(
        self,
    ):
        self.login_as_member_office_user()

        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        tapir_user.shift_user_data.save()

        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.shift_user_data.id]),
            data={"attendance_mode": ShiftAttendanceMode.FLYING},
        )
        self.assertRedirects(response, tapir_user.get_absolute_url())

        tapir_user.shift_user_data.refresh_from_db()
        self.assertEqual(
            ShiftAttendanceMode.FLYING,
            tapir_user.shift_user_data.attendance_mode,
            "The user's attendance should have been updated.",
        )

    def test_editShiftUserDataView_confirmUnregister_cancelsFutureAttendances(
        self,
    ):
        self.login_as_member_office_user()

        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        tapir_user.shift_user_data.save()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=1)
        slot_template: ShiftSlotTemplate = shift_template.slot_templates.first()
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=slot_template
        )

        now = datetime.datetime(year=2021, month=3, day=15)
        mock_timezone_now(self, now)

        past_shift = shift_template.create_shift(now - datetime.timedelta(days=30))
        future_shift = shift_template.create_shift(now + datetime.timedelta(days=30))
        for slot in ShiftSlot.objects.all():
            slot.update_attendance_from_template()

        url = reverse(self.VIEW_NAME, args=[tapir_user.shift_user_data.id])
        response = self.client.post(
            url,
            data={
                "attendance_mode": ShiftAttendanceMode.FLYING,
                "confirm_delete_abcd_attendance": True,
            },
        )
        self.assertRedirects(response, tapir_user.get_absolute_url())

        tapir_user.shift_user_data.refresh_from_db()
        self.assertEqual(
            ShiftAttendanceMode.FLYING,
            tapir_user.shift_user_data.attendance_mode,
            "The user's attendance should have been updated.",
        )
        self.assertFalse(
            ShiftAttendanceTemplate.objects.exists(),
            "The abcd attendance should have been deleted",
        )
        self.assertEqual(
            ShiftAttendance.State.PENDING,
            past_shift.get_attendances().first().state,
            "Attendance from past shifts should not get updated",
        )
        self.assertEqual(
            ShiftAttendance.State.CANCELLED,
            future_shift.get_attendances().first().state,
            "Attendance from future shifts should get cancelled",
        )

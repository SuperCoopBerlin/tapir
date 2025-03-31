from unittest.mock import patch, Mock

from django.template.response import TemplateResponse
from django.urls import reverse

from tapir import settings
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendance, ShiftSlot
from tapir.shifts.services.can_look_for_standin_service import CanLookForStandinService
from tapir.shifts.services.self_unregister_service import SelfUnregisterService
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, PermissionTestMixin


class TestCantAttendView(PermissionTestMixin, TapirFactoryTestBase):
    def permission_test_get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
            settings.GROUP_MEMBER_OFFICE,
            settings.GROUP_SHIFT_MANAGER,
        ]

    def permission_test_do_request(self):
        ShiftFactory.create()
        member_registered_to_the_shift = TapirUserFactory.create()
        attendance = ShiftAttendance.objects.create(
            user=member_registered_to_the_shift, slot=ShiftSlot.objects.get()
        )

        return self.client.get(
            reverse("shifts:attendance_cant_attend", args=[attendance.id])
        )

    @patch.object(CanLookForStandinService, "can_look_for_a_standin")
    @patch.object(SelfUnregisterService, "build_reasons_why_cant_self_unregister")
    def test_cantAttendView_default_contextDataIsCorrect(
        self,
        mock_build_reasons_why_cant_self_unregister: Mock,
        mock_can_look_for_a_standin: Mock,
    ):
        shift = ShiftFactory.create()
        member_registered_to_the_shift = self.login_as_normal_user()
        attendance = ShiftAttendance.objects.create(
            user=member_registered_to_the_shift, slot=shift.slots.get()
        )
        mock_build_reasons_why_cant_self_unregister.return_value = (
            "test reasons why cant self unregister"
        )
        mock_can_look_for_a_standin.return_value = "test can look for standin"

        response: TemplateResponse = self.client.get(
            reverse("shifts:attendance_cant_attend", args=[attendance.id])
        )

        self.assertStatusCode(response, 200)
        self.assertEqual(attendance, response.context_data["attendance"])
        mock_build_reasons_why_cant_self_unregister.assert_called_once_with(
            member_registered_to_the_shift, attendance
        )
        self.assertEqual(
            "test reasons why cant self unregister",
            response.context_data["reasons_why_cant_self_unregister"],
        )
        self.assertEqual(
            False,
            response.context_data["can_unregister"],
        )
        mock_can_look_for_a_standin.assert_called_once_with(shift.slots.get())
        self.assertEqual(
            "test can look for standin",
            response.context_data["can_look_for_standin"],
        )

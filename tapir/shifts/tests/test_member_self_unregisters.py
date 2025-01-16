import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
)
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.shifts.tests.utils import register_user_to_shift
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMemberSelfUnregisters(TapirFactoryTestBase):
    def test_member_self_unregisters(self):
        user = self.login_as_normal_user(share_owner__is_investing=False)
        start_time = timezone.now() + datetime.timedelta(
            days=Shift.NB_DAYS_FOR_SELF_UNREGISTER, hours=1
        )
        shift = ShiftFactory.create(start_time=start_time)

        register_user_to_shift(self.client, user, shift)
        attendance = ShiftAttendance.objects.get(slot__shift=shift, user=user)
        self.client.post(
            reverse(
                "shifts:update_shift_attendance_state",
                args=[attendance.id, ShiftAttendance.State.CANCELLED],
            )
        )

        self.assertEqual(
            ShiftAttendance.objects.get(slot__shift=shift, user=user).state,
            ShiftAttendance.State.CANCELLED,
            "The attendance state should have been set to cancelled",
        )
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "The user should not get negative points for cancelling",
        )

    def test_member_self_unregisters_threshold(self):
        user = self.login_as_normal_user(share_owner__is_investing=False)
        start_time = timezone.now() + datetime.timedelta(
            days=Shift.NB_DAYS_FOR_SELF_UNREGISTER - 1
        )
        shift = ShiftFactory.create(start_time=start_time)

        register_user_to_shift(self.client, user, shift)
        attendance = ShiftAttendance.objects.get(slot__shift=shift, user=user)
        response = self.client.post(
            reverse(
                "shifts:update_shift_attendance_state",
                args=[attendance.id, ShiftAttendance.State.CANCELLED],
            )
        )
        self.assertEqual(
            response.status_code,
            403,
            "The user should not be able to unregister themselves because the shift is too close to now",
        )

    def test_member_self_unregisters_abcd(self):
        user = self.login_as_normal_user()

        shift_template = ShiftTemplateFactory.create()
        slot_template = ShiftSlotTemplate.objects.filter(
            shift_template=shift_template
        ).first()
        ShiftAttendanceTemplate.objects.create(slot_template=slot_template, user=user)
        shift = shift_template.create_shift(
            timezone.now()
            + datetime.timedelta(days=Shift.NB_DAYS_FOR_SELF_UNREGISTER + 1)
        )

        attendance = ShiftAttendance.objects.get(slot__shift=shift, user=user)
        response = self.client.post(
            reverse(
                "shifts:update_shift_attendance_state",
                args=[attendance.id, ShiftAttendance.State.CANCELLED],
            )
        )
        self.assertEqual(
            response.status_code,
            403,
            "The user should not be able to unregister themselves because they are registered to the corresponding "
            "shift template.",
        )

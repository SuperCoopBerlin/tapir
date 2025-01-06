import datetime

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.stand_in_found_email import StandInFoundEmail
from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendance,
)
from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.tests.utils import register_user_to_shift
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class TestMemberSelfLookForStandIn(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_member_self_look_for_stand_in(self):
        user = self.login_as_normal_user()
        start_time = timezone.now() + datetime.timedelta(hours=1)
        shift = ShiftFactory.create(start_time=start_time)

        register_user_to_shift(self.client, user, shift)
        attendance = ShiftAttendance.objects.get(slot__shift=shift, user=user)
        self.client.post(
            reverse(
                "shifts:update_shift_attendance_state",
                args=[attendance.id, ShiftAttendance.State.LOOKING_FOR_STAND_IN],
            )
        )

        self.assertEqual(
            ShiftAttendance.objects.get(slot__shift=shift, user=user).state,
            ShiftAttendance.State.LOOKING_FOR_STAND_IN,
            "The attendance state should have been set to looking for a stand in.",
        )

    def test_member_self_look_for_stand_in_threshold(self):
        user = self.login_as_normal_user()
        start_time = timezone.now() + datetime.timedelta(hours=-1)
        shift = ShiftFactory.create(start_time=start_time)
        ShiftAttendance.objects.create(user=user, slot=ShiftSlot.objects.get())

        attendance = ShiftAttendance.objects.get(slot__shift=shift, user=user)
        response = self.client.post(
            reverse(
                "shifts:update_shift_attendance_state",
                args=[attendance.id, ShiftAttendance.State.LOOKING_FOR_STAND_IN],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
            f"The user should not be able to search of a stand-in because the shift is too close to now. {timezone.now()} {start_time}",
        )

    def test_stand_in_found(self):
        user_looking = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        start_time = timezone.now() + datetime.timedelta(days=1)
        shift = ShiftFactory.create(start_time=start_time)
        slot = ShiftSlot.objects.filter(shift=shift).first()
        ShiftAttendance.objects.create(
            user=user_looking,
            state=ShiftAttendance.State.LOOKING_FOR_STAND_IN,
            slot=ShiftSlot.objects.filter(shift=shift).first(),
        )

        user_replacing = self.login_as_normal_user()

        register_user_to_shift(self.client, user_replacing, shift)
        self.assertEqual(
            ShiftAttendance.objects.get(slot=slot, user=user_replacing).state,
            ShiftAttendance.State.PENDING,
            "The replacing user should be registered as normal.",
        )
        self.assertEqual(
            ShiftAttendance.objects.get(slot=slot, user=user_looking).state,
            ShiftAttendance.State.CANCELLED,
            "The attendance of the user that was looking for a stand-in should be cancelled.",
        )
        self.assertEqual(
            len(mail.outbox),
            1,
            "An email should have been sent to the email that was looking for a stand-in",
        )
        self.assertEmailOfClass_GotSentTo(
            StandInFoundEmail, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

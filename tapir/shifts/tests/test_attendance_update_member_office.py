import datetime

from django.core import mail
from django.urls import reverse

from tapir.accounts.models import TapirUser, OptionalMails
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.shift_confirmed_email import ShiftConfirmedEmailBuilder
from tapir.shifts.emails.shift_missed_email import ShiftMissedEmailBuilder
from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendance,
)
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class TestAttendanceUpdateMemberOffice(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_shift_attended(self):
        self.do_test(ShiftAttendance.State.DONE, 1)

    def test_shift_excused(self):
        self.do_test(ShiftAttendance.State.MISSED_EXCUSED, 1)

    def test_shift_missed(self):
        self.assertEqual(0, len(mail.outbox))
        self.do_test(ShiftAttendance.State.MISSED, -1)
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            ShiftMissedEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_shift_confirmed(self):
        self.assertEqual(0, len(mail.outbox))
        self.do_test(
            ShiftAttendance.State.DONE,
            1,
            optional_mail_enabled=ShiftConfirmedEmailBuilder.get_unique_id(),
        )
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            ShiftConfirmedEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_update_from_missed_to_attended(self):
        user: TapirUser = TapirUserFactory.create()
        shift = ShiftFactory.create()
        attendance = ShiftAttendance.objects.create(
            user=user, slot=ShiftSlot.objects.filter(shift=shift).first()
        )

        self.login_as_member_office_user()
        self.update_attendance_state(attendance, ShiftAttendance.State.MISSED)
        self.update_attendance_state(attendance, ShiftAttendance.State.DONE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            1,
            "After changing the attendance state from MISSED to DONE, the user's account balance should be 1.",
        )

    def test_create_manual_shift_account_entry(self):
        user = TapirUserFactory.create()
        self.login_as_member_office_user()
        response = self.client.post(
            reverse("shifts:create_shift_account_entry", args=[user.id]),
            {
                "date": datetime.datetime.now(),
                "value": 2,
                "description": "A TEST DESCRIPTION",
            },
        )
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            2,
            "After creating a manual entry, the user's balance should be 2.",
        )
        self.assertRedirects(
            response,
            user.get_absolute_url(),
            msg_prefix="The call should redirect to the user's page.",
        )

    def do_test(
        self,
        target_state,
        expected_account_balance,
        optional_mail_enabled: str | None = None,
    ):
        user: TapirUser = TapirUserFactory.create(
            preferred_language="de", email=self.USER_EMAIL_ADDRESS
        )
        if optional_mail_enabled:
            OptionalMails.objects.create(
                user=user,
                mail_id=optional_mail_enabled,
                choice=True,
            )
        shift = ShiftFactory.create()
        attendance = ShiftAttendance.objects.create(
            user=user, slot=ShiftSlot.objects.filter(shift=shift).first()
        )

        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "We assume that the user starts with a 0 balance.",
        )

        self.login_as_member_office_user()
        response = self.update_attendance_state(attendance, target_state)

        self.assertEqual(
            ShiftAttendance.objects.get(id=attendance.id).state,
            target_state,
            "The attendance's state have been updated to the target_state.",
        )
        self.assertRedirects(
            response,
            attendance.slot.shift.get_absolute_url(),
            msg_prefix="The call should redirect to the shift's page.",
        )
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            expected_account_balance,
            f"After updating the attendance state to {target_state}, the user's account balance should be {expected_account_balance}.",
        )

    def update_attendance_state(self, attendance, target_state):
        return self.client.post(
            reverse(
                "shifts:update_shift_attendance_state",
                args=[attendance.id, target_state],
            )
        )

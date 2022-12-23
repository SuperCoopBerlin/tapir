import datetime

from django.core import mail
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmail
from tapir.shifts.management.commands.send_shift_reminders import Command
from tapir.shifts.models import ShiftAttendance, Shift
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase


class TestShiftReminder(TapirFactoryTestBase, TapirEmailTestBase):
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_shift_in_the_past_does_not_trigger_reminder(self):
        user: TapirUser = TapirUserFactory.create()
        shift_in_the_past: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=-3)
        )
        ShiftAttendance.objects.create(
            user=user, slot=shift_in_the_past.slots.first(), reminder_email_sent=False
        )

        Command.send_shift_reminder_for_user(user.shift_user_data)

        self.assertEqual(
            0,
            len(mail.outbox),
            "A shift that is in the past should not get a reminder even if the reminder has never been sent.",
        )

    def test_shift_too_far_in_the_future_does_not_trigger_reminder(self):
        user: TapirUser = TapirUserFactory.create()
        shift_far_in_the_future: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=8)
        )
        attendance = ShiftAttendance.objects.create(
            user=user,
            slot=shift_far_in_the_future.slots.first(),
            reminder_email_sent=False,
        )

        Command.send_shift_reminder_for_user(user.shift_user_data)

        self.assertEqual(
            0,
            len(mail.outbox),
            "A shift that is too far in the future should not get a reminder.",
        )
        attendance.refresh_from_db()
        self.assertFalse(attendance.reminder_email_sent)

    def test_shift_in_the_near_future_triggers_a_reminder(self):
        user: TapirUser = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        shift_in_the_near_future: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=6)
        )
        attendance = ShiftAttendance.objects.create(
            user=user,
            slot=shift_in_the_near_future.slots.first(),
            reminder_email_sent=False,
        )

        Command.send_shift_reminder_for_user(user.shift_user_data)

        self.assertEqual(
            1,
            len(mail.outbox),
            "A shift that is in the new future should get a reminder.",
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftReminderEmail, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )
        attendance.refresh_from_db()
        self.assertTrue(attendance.reminder_email_sent)

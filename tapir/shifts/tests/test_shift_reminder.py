import datetime

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.second_shift_reminder_email import (
    SecondShiftReminderEmailBuilder,
)
from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmailBuilder
from tapir.shifts.models import ShiftAttendance, Shift
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class TestShiftReminder(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_shift_in_the_past_does_not_trigger_reminder(self):
        user: TapirUser = TapirUserFactory.create()
        shift_in_the_past: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=-3)
        )
        ShiftAttendance.objects.create(
            user=user, slot=shift_in_the_past.slots.first(), reminder_email_sent=False
        )

        call_command("send_shift_reminders")

        self.assertEqual(
            0,
            len(mail.outbox),
            "A shift that is in the past should not get a reminder even if the reminder has never been sent.",
        )

    def test_shift_too_far_in_the_future_does_not_trigger_reminder(self):
        user: TapirUser = TapirUserFactory.create()
        shift_far_in_the_future: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=10)
        )
        attendance = ShiftAttendance.objects.create(
            user=user,
            slot=shift_far_in_the_future.slots.first(),
            reminder_email_sent=False,
        )

        call_command("send_shift_reminders")

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

        call_command("send_shift_reminders")

        self.assertEqual(
            1,
            len(mail.outbox),
            "A shift that is in the new future should get a reminder.",
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftReminderEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )
        attendance.refresh_from_db()
        self.assertTrue(attendance.reminder_email_sent)

    def test_shift_in_the_very_near_future_triggers_a_second_reminder(self):
        if not settings.ENABLE_RIZOMA_CONTENT:
            self.skipTest("This test is only relevant for rizoma")

        user: TapirUser = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        shift_in_the_near_future: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=1)
        )
        attendance = ShiftAttendance.objects.create(
            user=user,
            slot=shift_in_the_near_future.slots.first(),
            reminder_email_sent=True,
            second_reminder_email_sent=False,
        )

        call_command("send_shift_reminders")

        self.assertEqual(
            1,
            len(mail.outbox),
            "A shift that is in the new future should get a reminder.",
        )
        self.assertEmailOfClass_GotSentTo(
            SecondShiftReminderEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )
        attendance.refresh_from_db()
        self.assertTrue(attendance.second_reminder_email_sent)

    def test_if_rizoma_content_is_disabled_second_reminders_should_not_be_sent(self):
        if settings.ENABLE_RIZOMA_CONTENT:
            self.skipTest("This test is only relevant for supercoop")

        user: TapirUser = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        shift_in_the_near_future: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=1)
        )
        attendance = ShiftAttendance.objects.create(
            user=user,
            slot=shift_in_the_near_future.slots.first(),
            reminder_email_sent=True,
            second_reminder_email_sent=False,
        )

        call_command("send_shift_reminders")

        self.assertEqual(
            0,
            len(mail.outbox),
            "A shift that is in the new future should get a reminder.",
        )
        self.assertFalse(attendance.second_reminder_email_sent)

    def test_if_both_reminders_could_be_send_only_one_should_be_sent(self):
        if not settings.ENABLE_RIZOMA_CONTENT:
            self.skipTest("This test is only relevant for rizoma")

        user: TapirUser = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        shift_in_the_near_future: Shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=1)
        )
        attendance = ShiftAttendance.objects.create(
            user=user,
            slot=shift_in_the_near_future.slots.first(),
            reminder_email_sent=False,
            second_reminder_email_sent=False,
        )

        call_command("send_shift_reminders")
        call_command("send_shift_reminders")

        self.assertEqual(
            1,
            len(mail.outbox),
            "A shift that is in the new future should get a reminder.",
        )
        self.assertEmailOfClass_GotSentTo(
            SecondShiftReminderEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )
        attendance.refresh_from_db()
        self.assertTrue(attendance.second_reminder_email_sent)

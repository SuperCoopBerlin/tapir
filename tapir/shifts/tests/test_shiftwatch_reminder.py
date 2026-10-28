import datetime

from django.core import mail
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.shift_watch_mail import ShiftWatchEmailBuilder
from tapir.shifts.management.commands.send_understaffed_shift_reminder_mail import (
    Command as ReminderCommand,
)
from tapir.shifts.models import ShiftSlot, ShiftUserCapability, StaffingStatusChoices
from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.tests.test_shiftwatch_notification import (
    create_shift_watch,
    create_shift_with_attendance,
)
from tapir.utils.tests_utils import TapirEmailTestMixin, TapirFactoryTestBase


class ShiftWatchReminderCommandTests(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"
    NUM_REQUIRED_ATTENDANCE = 2

    def setUp(self):
        self.user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        # create shift empty from the beginning
        self.shift = ShiftFactory.create(
            nb_slots=3,
            num_required_attendances=self.NUM_REQUIRED_ATTENDANCE,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=1, hours=2),
        )

    def assert_email_sent(self, expected_status_choice: str):
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(expected_status_choice), mail.outbox[0].body)
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_reminder_understaffedShift_mailIsSent(self):
        create_shift_watch(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            last_staffing_status=None,
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
            watched_capabilities=[],
        )

        ReminderCommand().handle()

        self.assert_email_sent(StaffingStatusChoices.UNDERSTAFFED.label)

    def test_reminder_noStaffingStatusSelected_noMailSent(self):

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[],
            watched_capabilities=[],
        )

        ReminderCommand().handle()

        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_understaffedNotInWatchedStatus_noMailSent(self):

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[StaffingStatusChoices.ALL_CLEAR],
            watched_capabilities=[],
        )

        ReminderCommand().handle()

        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_shiftNotTomorrow_noMailSent(self):

        self.shift.start_time = timezone.now() + datetime.timedelta(days=2)
        self.shift.end_time = timezone.now() + datetime.timedelta(days=2, hours=2)
        self.shift.save()

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
            watched_capabilities=[],
        )

        ReminderCommand().handle()

        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_shiftIsStaffed_noMailSent(self):

        shift, slots = create_shift_with_attendance(self.NUM_REQUIRED_ATTENDANCE)
        shift.start_time = timezone.now() + datetime.timedelta(days=1)
        shift.end_time = timezone.now() + datetime.timedelta(days=1, hours=2)
        shift.save()

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=shift,
            last_valid_slot_ids=slots,
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
            watched_capabilities=[],
        )

        ReminderCommand().handle()

        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_withWatchedCapabilities_noMailSent(self):

        ShiftSlot.objects.create(
            shift=self.shift,
            name="cheese-making",
            required_capabilities=[ShiftUserCapability.SHIFT_COORDINATOR],
        )

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[],
            watched_capabilities=[ShiftUserCapability.SHIFT_COORDINATOR],
        )

        ReminderCommand().handle()

        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_multipleWatches_mailSentForEach(self):

        user2 = TapirUserFactory.create(email="test2@test.net")
        shift2 = ShiftFactory.create(
            nb_slots=3,
            num_required_attendances=self.NUM_REQUIRED_ATTENDANCE,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=1, hours=2),
        )

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
            watched_capabilities=[],
        )

        create_shift_watch(
            user=user2,
            shift=shift2,
            last_valid_slot_ids=[],
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
            watched_capabilities=[],
        )

        ReminderCommand().handle()

        self.assertEqual(len(mail.outbox), 2)

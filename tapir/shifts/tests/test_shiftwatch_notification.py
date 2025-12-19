import datetime

import pytest
from django.core import mail
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.shift_watch_mail import ShiftWatchEmailBuilder
from tapir.shifts.management.commands.send_shift_watch_mail import Command
from tapir.shifts.models import (
    ShiftWatch,
    StaffingStatusChoices,
    ShiftSlot,
    ShiftUserCapability,
    get_staffingstatus_choices,
    ShiftAttendance,
)

from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


def create_shift_with_attendance(num_attendances):
    shift = ShiftFactory.create(
        nb_slots=3,
        num_required_attendances=num_attendances,
        start_time=timezone.now() + datetime.timedelta(days=1),
        end_time=timezone.now() + datetime.timedelta(days=1, hours=2),
    )
    slots = {}
    for _ in range(num_attendances):
        slot = ShiftSlot.objects.create(shift=shift, name="cheese-making")
        user = TapirUserFactory.create()
        ShiftAttendance.objects.create(user=user, slot=slot)
        slots[user] = slot.pk
    return shift, slots


class ShiftWatchCommandTests(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"
    NUM_REQUIRED_ATTENDANCE = 2

    def setUp(self):
        self.user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        self.shift_ok_first, self.slots = create_shift_with_attendance(
            self.NUM_REQUIRED_ATTENDANCE
        )

    def unregister_first_slot(self):
        first_user, first_slot = next(iter(self.slots.items()))
        ShiftAttendance.objects.filter(slot=first_slot, user=first_user).update(
            state=ShiftAttendance.State.LOOKING_FOR_STAND_IN
        )

    def assert_email_sent(self, expected_status_choice):
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(expected_status_choice.label), mail.outbox[0].body)
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_watchedShiftIsUnderstaffed_correctNotificationIsSent(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift_ok_first,
            last_valid_slot_ids=list(self.slots.values()),
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )
        Command().handle()
        self.assertEqual(0, len(mail.outbox))

        self.unregister_first_slot()
        Command().handle()
        self.assert_email_sent(StaffingStatusChoices.UNDERSTAFFED)

    def test_handle_watchedShiftIsAlright_noNotificationIsSent(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift_ok_first,
            last_valid_slot_ids=list(self.slots.values()),
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )
        Command().handle()
        self.assertEqual(0, len(mail.outbox))

    def test_handle_watchingCoordinatorChanges_SHIFT_COORDINATOR_PLUSGetSent(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift_ok_first,
            last_valid_slot_ids=list(self.slots.values()),
            staffing_status=[StaffingStatusChoices.SHIFT_COORDINATOR_PLUS.value],
        )

        slot = ShiftSlot.objects.filter(
            shift=self.shift_ok_first, attendances__isnull=True
        ).first()
        slot.required_capabilities = [ShiftUserCapability.SHIFT_COORDINATOR]
        slot.save()

        Command().handle()
        self.assertEqual(0, len(mail.outbox))

        # Register teamleader
        ShiftAttendance.objects.create(user=TapirUserFactory.create(), slot=slot)
        Command().handle()

        self.assertEqual(1, len(mail.outbox))
        self.assertIn(
            str(StaffingStatusChoices.SHIFT_COORDINATOR_PLUS.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_initialWatchUnderstaffedShift_noInitialMailIsSent(self):
        # No initial message should be sent, even if the shift is understaffed
        user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)

        shift_understaffed, slots = create_shift_with_attendance(
            self.NUM_REQUIRED_ATTENDANCE - 1
        )

        ShiftWatch.objects.create(
            user=user,
            shift=shift_understaffed,
            last_valid_slot_ids=list(slots.values()),
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        Command().handle()
        self.assertEqual(len(mail.outbox), 0)

        new_slot = ShiftSlot.objects.create(
            shift=shift_understaffed, name="cheese-making"
        )
        ShiftAttendance.objects.create(user=TapirUserFactory.create(), slot=new_slot)

        Command().handle()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(StaffingStatusChoices.ALL_CLEAR.label), mail.outbox[0].body)

    def test_handle_triggeredMultipleTimes_onlyOneMailIsSent(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift_ok_first,
            last_valid_slot_ids=list(self.slots.values()),
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )

        self.unregister_first_slot()

        self.assertEqual(len(mail.outbox), 0)

        for _ in range(3):
            Command().handle()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            str(StaffingStatusChoices.UNDERSTAFFED.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_watchedShiftIsCurrentlyRunning_correctNotificationIsSent(self):
        self.shift_ok_first.start_time = timezone.now() - datetime.timedelta(hours=2)
        self.shift_ok_first.end_time = timezone.now() + datetime.timedelta(hours=2)
        self.shift_ok_first.save()

        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift_ok_first,
            last_valid_slot_ids=list(self.slots.values()),
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        self.unregister_first_slot()

        Command().handle()

        self.assertEqual(1, len(mail.outbox))
        self.assertIn(
            str(StaffingStatusChoices.UNDERSTAFFED.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_shiftInThePast_noNotification(self):

        self.shift_ok_first.start_time = timezone.now() - datetime.timedelta(days=10)
        self.shift_ok_first.end_time = timezone.now() - datetime.timedelta(
            days=9, hours=22
        )
        self.shift_ok_first.save()

        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift_ok_first,
            last_valid_slot_ids=list(self.slots.values()),
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        self.unregister_first_slot()

        Command().handle()

        self.assertEqual(len(mail.outbox), 0)

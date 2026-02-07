import datetime

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
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator

from tapir.shifts.tests.factories import ShiftFactory, ShiftWatchFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


def create_shift_with_attendance(num_attendances):
    shift = ShiftFactory.create(
        nb_slots=3,
        num_required_attendances=num_attendances,
        start_time=timezone.now() + datetime.timedelta(days=1),
        end_time=timezone.now() + datetime.timedelta(days=1, hours=2),
    )
    slots = []
    for _ in range(num_attendances):
        slot = ShiftSlot.objects.create(shift=shift, name="cheese-making")
        user = TapirUserFactory.create()
        ShiftAttendance.objects.create(user=user, slot=slot)
        slots.append(slot.pk)
    return shift, slots


def create_shift_watch(
    user, shift, slots, last_staffing_status=None, staffing_status=None
):
    if last_staffing_status is None:
        last_staffing_status = ShiftWatchCreator.get_initial_staffing_status_for_shift(
            shift=shift
        )
    if staffing_status is None:
        staffing_status = [event.value for event in get_staffingstatus_choices()]
    return ShiftWatchFactory(
        user=user,
        shift=shift,
        last_valid_slot_ids=slots,
        staffing_status=staffing_status,
        last_staffing_status=last_staffing_status,
    )


class ShiftWatchCommandTests(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"
    NUM_REQUIRED_ATTENDANCE = 2

    def setUp(self):
        self.user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        self.shift_ok_first, self.slots = create_shift_with_attendance(
            self.NUM_REQUIRED_ATTENDANCE
        )

    def unregister_first_slot(self):
        first_slot = self.slots[0]
        first_shift_attendance = ShiftAttendance.objects.filter(slot=first_slot).first()
        first_shift_attendance.state = ShiftAttendance.State.LOOKING_FOR_STAND_IN
        first_shift_attendance.save()

    def assert_email_sent(self, expected_status_choice):
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(expected_status_choice.label), mail.outbox[0].body)
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_watchedShiftIsUnderstaffed_correctNotificationIsSent(self):
        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift_ok_first,
            slots=self.slots,
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )
        Command().handle()
        self.assertEqual(0, len(mail.outbox))

        self.unregister_first_slot()
        Command().handle()
        self.assert_email_sent(StaffingStatusChoices.UNDERSTAFFED)

    def test_handle_watchedShiftIsAlright_noNotificationIsSent(self):
        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift_ok_first,
            slots=self.slots,
            staffing_status=list(get_staffingstatus_choices()),
        )
        Command().handle()
        self.assertEqual(0, len(mail.outbox))

    def test_handle_watchingCoordinatorChanges_SHIFT_COORDINATOR_PLUSGetSent(self):
        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift_ok_first,
            slots=self.slots,
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
        self.assert_email_sent(StaffingStatusChoices.SHIFT_COORDINATOR_PLUS)

    def test_handle_initialWatchUnderstaffedShift_noInitialMailIsSent(self):
        # No initial message should be sent, even if the shift is understaffed
        user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)

        shift_understaffed, slots = create_shift_with_attendance(
            self.NUM_REQUIRED_ATTENDANCE - 1
        )

        create_shift_watch(
            user=user,
            shift=shift_understaffed,
            slots=slots,
            last_staffing_status=ShiftWatchCreator.get_initial_staffing_status_for_shift(
                shift=shift_understaffed
            ),
        )

        Command().handle()
        self.assertEqual(len(mail.outbox), 0)

        new_slot = ShiftSlot.objects.create(
            shift=shift_understaffed, name="cheese-making"
        )
        ShiftAttendance.objects.create(user=TapirUserFactory.create(), slot=new_slot)

        Command().handle()

        self.assert_email_sent(StaffingStatusChoices.ALL_CLEAR)

    def test_handle_triggeredMultipleTimes_onlyOneMailIsSent(self):
        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift_ok_first,
            slots=self.slots,
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )

        self.unregister_first_slot()

        self.assertEqual(len(mail.outbox), 0)

        for _ in range(3):
            Command().handle()

        self.assert_email_sent(StaffingStatusChoices.UNDERSTAFFED)

    def test_handle_watchedShiftIsCurrentlyRunning_correctNotificationIsSent(self):
        self.shift_ok_first.start_time = timezone.now() - datetime.timedelta(hours=4)
        self.shift_ok_first.end_time = timezone.now() + datetime.timedelta(hours=4)
        self.shift_ok_first.save()

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift_ok_first,
            slots=self.slots,
            staffing_status=[StaffingStatusChoices.UNDERSTAFFED],
        )

        self.unregister_first_slot()

        Command().handle()
        self.assert_email_sent(StaffingStatusChoices.UNDERSTAFFED)

    def test_handle_shiftInThePast_noNotification(self):

        self.shift_ok_first.start_time = timezone.now() - datetime.timedelta(days=10)
        self.shift_ok_first.end_time = timezone.now() - datetime.timedelta(
            days=9, hours=22
        )
        self.shift_ok_first.save()

        self.shift_watch = create_shift_watch(
            user=self.user,
            shift=self.shift_ok_first,
            slots=self.slots,
        )

        self.unregister_first_slot()

        Command().handle()

        self.assertEqual(len(mail.outbox), 0)

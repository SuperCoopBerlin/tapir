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

from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.tests.utils import register_user_to_shift
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class ShiftWatchCommandTests(TapirFactoryTestBase, TapirEmailTestMixin):
    USER_EMAIL_ADDRESS = "test_address@test.net"
    NUM_REQUIRED_ATTENDANCE = 2

    def setUp(self):
        self.user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        self.shift = ShiftFactory.create(
            nb_slots=3,
            num_required_attendances=self.NUM_REQUIRED_ATTENDANCE,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=1, hours=2),
        )

    def test_handle_watchedShiftIsUnderstaffed_correctNotificationIsSent(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        register_user_to_shift(self.client, TapirUserFactory.create(), self.shift)

        self.assertEqual(0, len(mail.outbox))
        Command().handle()
        self.assertEqual(1, len(mail.outbox))

        self.assertIn(
            str(StaffingStatusChoices.UNDERSTAFFED.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_watchedShiftIsAlright_noNotificationIsSent(self):
        slots = []
        for _ in range(self.NUM_REQUIRED_ATTENDANCE):
            slot = ShiftSlot.objects.create(shift=self.shift, name="cheese-making")
            user = TapirUserFactory.create()
            ShiftAttendance.objects.create(user=user, slot=slot)
            slots.append(slot)

        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[slot.id for slot in slots],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )
        Command().handle()
        self.assertEqual(0, len(mail.outbox))

    def test_handle_watchingCoordinatorChanges_coordinatorNotificationsGetSent(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[StaffingStatusChoices.SHIFT_COORDINATOR_PLUS.value],
        )

        self.shift.num_required_attendances = 0  # 0 required
        slot = ShiftSlot.objects.filter(
            shift=self.shift, attendances__isnull=True
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

    def test_handle_triggeredMultipleTimes_onlyOneMailIsSend(self):
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        register_user_to_shift(self.client, TapirUserFactory.create(), self.shift)

        self.assertEqual(0, len(mail.outbox))
        Command().handle()
        Command().handle()
        Command().handle()
        self.assertEqual(1, len(mail.outbox))

        self.assertIn(
            str(StaffingStatusChoices.UNDERSTAFFED.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_shiftInThePast_noNotification(self):
        self.shift.start_time = timezone.now() - datetime.timedelta(days=10)
        self.shift.end_time = timezone.now() - datetime.timedelta(days=9, hours=22)
        self.shift.save()
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        register_user_to_shift(self.client, TapirUserFactory.create(), self.shift)
        Command().handle()
        self.assertEqual(0, len(mail.outbox))

    def test_handle_ATTENDANCE_PLUS_onlySentIfThereAreNoOtherChanges(self):
        slots = []
        for _ in range(self.NUM_REQUIRED_ATTENDANCE):
            slot = ShiftSlot.objects.create(shift=self.shift, name="cheese-making")
            user = TapirUserFactory.create()
            ShiftAttendance.objects.create(user=user, slot=slot)
            slots.append(slot)

        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[slot.id for slot in slots],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        # register one extra slot
        slot = ShiftSlot.objects.create(shift=self.shift, name="cheese-making")
        user = TapirUserFactory.create()
        ShiftAttendance.objects.create(user=user, slot=slot)
        Command().handle()

        self.assertIn(
            str(StaffingStatusChoices.ATTENDANCE_PLUS.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_ATTENDANCE_MINUS_onlySentIfThereAreNoOtherChanges(self):
        slots = []
        for _ in range(self.NUM_REQUIRED_ATTENDANCE + 1):
            slot = ShiftSlot.objects.create(shift=self.shift, name="cheese-making")
            user = TapirUserFactory.create()
            attendance = ShiftAttendance.objects.create(user=user, slot=slot)
            slots.append(slot)

        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[slot.id for slot in slots],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )
        attendance.state = ShiftAttendance.State.LOOKING_FOR_STAND_IN
        attendance.save()

        Command().handle()
        self.assertIn(
            str(StaffingStatusChoices.ATTENDANCE_MINUS.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

    def test_handle_watchedShiftIsCurrentlyRunning_correctNotificationIsSent(self):
        self.shift.start_time = timezone.now() - datetime.timedelta(hours=2)
        self.shift.end_time = timezone.now() + datetime.timedelta(hours=2)
        self.shift.save()
        self.shift_watch = ShiftWatch.objects.create(
            user=self.user,
            shift=self.shift,
            last_valid_slot_ids=[],
            staffing_status=[event.value for event in get_staffingstatus_choices()],
        )

        register_user_to_shift(self.client, TapirUserFactory.create(), self.shift)

        self.assertEqual(0, len(mail.outbox))
        Command().handle()
        self.assertEqual(1, len(mail.outbox))

        self.assertIn(
            str(StaffingStatusChoices.UNDERSTAFFED.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

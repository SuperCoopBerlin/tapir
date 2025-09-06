import pytest
from django.core import mail

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

    def setUp(self):
        self.user = TapirUserFactory.create(email=self.USER_EMAIL_ADDRESS)
        self.shift = ShiftFactory.create(nb_slots=3, num_required_attendances=2)

    def test_handle_understaffed_notification(self):
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

    def test_handle_shift_coordinator_registered_notification(self):
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

        self.assertEqual(1, len(mail.outbox))  # SHIFT_PLUS und SHIFT_COORDINATOR_PLUS
        self.assertIn(
            str(StaffingStatusChoices.SHIFT_COORDINATOR_PLUS.label), mail.outbox[0].body
        )
        self.assertEmailOfClass_GotSentTo(
            ShiftWatchEmailBuilder, self.USER_EMAIL_ADDRESS, mail.outbox[0]
        )

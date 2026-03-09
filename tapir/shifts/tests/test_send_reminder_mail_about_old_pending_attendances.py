import datetime

from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.core.models import FeatureFlag
from tapir.shifts.config import FEATURE_FLAG_REMINDER_MAIL_OLD_PENDING_ATTENDANCES
from tapir.shifts.models import ShiftAttendance
from tapir.shifts.tests.factories import ShiftSlotFactory, ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSendReminderMailAboutOldPendingAttendances(TapirFactoryTestBase):
    def setup_test_data(self):
        FeatureFlag.objects.create(
            flag_name=FEATURE_FLAG_REMINDER_MAIL_OLD_PENDING_ATTENDANCES,
            flag_value=True,
        )

        shift_old_enough = ShiftFactory.create(
            start_time=timezone.now() - datetime.timedelta(days=15)
        )

        slot = ShiftSlotFactory.create(shift=shift_old_enough)
        self.attendance_that_should_be_included_1 = ShiftAttendance.objects.create(
            slot=slot,
            user=TapirUserFactory.create(),
            state=ShiftAttendance.State.PENDING,
        )
        slot = ShiftSlotFactory.create(shift=shift_old_enough)
        self.attendance_that_should_be_included_2 = ShiftAttendance.objects.create(
            slot=slot,
            user=TapirUserFactory.create(),
            state=ShiftAttendance.State.LOOKING_FOR_STAND_IN,
        )

        slot = ShiftSlotFactory.create(shift=shift_old_enough)
        self.attendance_that_is_not_pending = ShiftAttendance.objects.create(
            slot=slot, user=TapirUserFactory.create(), state=ShiftAttendance.State.DONE
        )

        shift_not_old_enough = ShiftFactory.create(
            start_time=timezone.now() - datetime.timedelta(days=13)
        )
        slot = ShiftSlotFactory.create(shift=shift_not_old_enough)
        self.attendance_that_is_not_old_enough_yet = ShiftAttendance.objects.create(
            slot=slot,
            user=TapirUserFactory.create(),
            state=ShiftAttendance.State.PENDING,
        )

    def test_commandSendReminderMailAboutOldPendingAttendances_featureFlagDisabled_noMailSent(
        self,
    ):
        self.setup_test_data()
        FeatureFlag.objects.filter(
            flag_name=FEATURE_FLAG_REMINDER_MAIL_OLD_PENDING_ATTENDANCES
        ).update(flag_value=False)

        call_command("send_reminder_mail_about_old_pending_attendances")

        self.assertEqual(0, len(mail.outbox))

    def test_commandSendReminderMailAboutOldPendingAttendances_noPendingAttendance_noMailSent(
        self,
    ):
        self.setup_test_data()
        self.attendance_that_should_be_included_1.delete()
        self.attendance_that_should_be_included_2.delete()

        call_command("send_reminder_mail_about_old_pending_attendances")

        self.assertEqual(0, len(mail.outbox))

    def test_commandSendReminderMailAboutOldPendingAttendances_pendingAttendancesExist_mailSent(
        self,
    ):
        self.setup_test_data()

        call_command("send_reminder_mail_about_old_pending_attendances")

        self.assertEqual(1, len(mail.outbox))

        mail_content = mail.outbox[0].body

        self.assertIn(
            self.attendance_that_should_be_included_1.slot.get_display_name(),
            mail_content,
        )
        self.assertIn(
            self.attendance_that_should_be_included_2.slot.get_display_name(),
            mail_content,
        )

        self.assertNotIn(
            self.attendance_that_is_not_pending.slot.get_display_name(),
            mail_content,
        )
        self.assertNotIn(
            self.attendance_that_is_not_old_enough_yet.slot.get_display_name(),
            mail_content,
        )

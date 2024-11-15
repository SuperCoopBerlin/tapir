import datetime
from unittest.mock import patch, Mock

from django.core import mail
from django.core.management import call_command

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.log.models import EmailLogEntry
from tapir.shifts.config import FEATURE_FLAG_FLYING_MEMBERS_REGISTRATION_REMINDER
from tapir.shifts.emails.flying_member_registration_reminder_email import (
    FlyingMemberRegistrationReminderEmail,
)
from tapir.shifts.management.commands.send_flying_member_registration_reminder_mails import (
    Command,
)
from tapir.shifts.models import ShiftAttendanceMode, ShiftUserData, ShiftAttendance
from tapir.shifts.services.shift_cycle_service import ShiftCycleService
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    TapirEmailTestBase,
    mock_timezone_now,
    FeatureFlagTestMixin,
)


class TestAttendanceUpdateMemberOffice(
    FeatureFlagTestMixin, TapirFactoryTestBase, TapirEmailTestBase
):
    NOW = datetime.datetime(year=2024, month=6, day=15)

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)
        self.given_feature_flag_value(
            FEATURE_FLAG_FLYING_MEMBERS_REGISTRATION_REMINDER, True
        )

    @patch.object(ShiftCycleService, "get_start_date_of_current_cycle")
    def test_sendFlyingMemberRegistrationReminderMailsCommand_featureFlagDisabled_noMailSent(
        self,
        mock_get_start_date_of_current_cycle: Mock,
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_FLYING_MEMBERS_REGISTRATION_REMINDER, False
        )

        call_command("send_flying_member_registration_reminder_mails")

        mock_get_start_date_of_current_cycle.filter.assert_not_called()
        self.assertEqual(0, len(mail.outbox))

    @patch.object(ShiftCycleService, "get_start_date_of_current_cycle")
    @patch.object(ShiftUserData, "objects")
    def test_sendFlyingMemberRegistrationReminderMailsCommand_todayIsCloseToEndOfCycle_noMailSent(
        self,
        mock_objects: Mock,
        mock_get_start_date_of_current_cycle: Mock,
    ):
        mock_get_start_date_of_current_cycle.return_value = (
            self.NOW - datetime.timedelta(days=25)
        ).date()

        call_command("send_flying_member_registration_reminder_mails")

        mock_objects.filter.assert_not_called()
        self.assertEqual(0, len(mail.outbox))

    @patch.object(ShiftCycleService, "get_start_date_of_current_cycle")
    @patch.object(Command, "should_member_receive_reminder_mail")
    def test_sendFlyingMemberRegistrationReminderMailsCommand_userNotFlying_noMailSent(
        self,
        mock_should_member_receive_reminder_mail: Mock,
        mock_get_start_date_of_current_cycle: Mock,
    ):
        mock_get_start_date_of_current_cycle.return_value = (
            self.NOW - datetime.timedelta(days=7)
        ).date()

        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        tapir_user.shift_user_data.save()

        call_command("send_flying_member_registration_reminder_mails")

        mock_should_member_receive_reminder_mail.assert_not_called()
        self.assertEqual(0, len(mail.outbox))

    @patch.object(ShiftCycleService, "get_start_date_of_current_cycle")
    @patch.object(Command, "should_member_receive_reminder_mail")
    def test_sendFlyingMemberRegistrationReminderMailsCommand_userShouldNotReceiveMail_noMailSent(
        self,
        mock_should_member_receive_reminder_mail: Mock,
        mock_get_start_date_of_current_cycle: Mock,
    ):
        cycle_start_date = (self.NOW - datetime.timedelta(days=7)).date()
        mock_get_start_date_of_current_cycle.return_value = cycle_start_date
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        tapir_user.shift_user_data.save()
        mock_should_member_receive_reminder_mail.return_value = False

        call_command("send_flying_member_registration_reminder_mails")

        mock_should_member_receive_reminder_mail.assert_called_once_with(
            tapir_user.shift_user_data, cycle_start_date
        )
        self.assertEqual(0, len(mail.outbox))

    @patch.object(ShiftCycleService, "get_start_date_of_current_cycle")
    @patch.object(Command, "should_member_receive_reminder_mail")
    def test_sendFlyingMemberRegistrationReminderMailsCommand_userShouldReceiveMail_mailSent(
        self,
        mock_should_member_receive_reminder_mail: Mock,
        mock_get_start_date_of_current_cycle: Mock,
    ):
        cycle_start_date = (self.NOW - datetime.timedelta(days=7)).date()
        mock_get_start_date_of_current_cycle.return_value = cycle_start_date
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        tapir_user.shift_user_data.save()
        mock_should_member_receive_reminder_mail.return_value = True

        call_command("send_flying_member_registration_reminder_mails")

        mock_should_member_receive_reminder_mail.assert_called_once_with(
            tapir_user.shift_user_data, cycle_start_date
        )
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            FlyingMemberRegistrationReminderEmail, tapir_user.email, mail.outbox[0]
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    def test_shouldMemberReceiveReminderMail_memberNotExpectedToDoShifts_returnsFalse(
        self, mock_is_member_expected_to_do_shifts: Mock
    ):
        shift_user_data = Mock()
        mock_is_member_expected_to_do_shifts.return_value = False

        result = Command.should_member_receive_reminder_mail(
            shift_user_data, self.NOW.date()
        )

        self.assertFalse(result)
        mock_is_member_expected_to_do_shifts.assert_called_once_with(shift_user_data)

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(Command, "has_user_received_reminder_this_cycle")
    def test_shouldMemberReceiveReminderMail_memberAlreadyReceivedMailThisCycle_returnsFalse(
        self,
        mock_has_user_received_reminder_this_cycle: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        shift_user_data = Mock()
        mock_is_member_expected_to_do_shifts.return_value = True
        mock_has_user_received_reminder_this_cycle.return_value = True
        start_date = Mock()

        result = Command.should_member_receive_reminder_mail(
            shift_user_data, start_date
        )

        self.assertFalse(result)
        mock_is_member_expected_to_do_shifts.assert_called_once_with(shift_user_data)
        mock_has_user_received_reminder_this_cycle.assert_called_once_with(
            shift_user_data, start_date
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(Command, "has_user_received_reminder_this_cycle")
    @patch.object(Command, "is_member_registered_to_a_shift_this_cycle")
    def test_shouldMemberReceiveReminderMail_memberAlreadyRegisteredToAShiftThisCycle_returnsFalse(
        self,
        mock_is_member_registered_to_a_shift_this_cycle: Mock,
        mock_has_user_received_reminder_this_cycle: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        shift_user_data = Mock()
        mock_is_member_expected_to_do_shifts.return_value = True
        mock_has_user_received_reminder_this_cycle.return_value = False
        mock_is_member_registered_to_a_shift_this_cycle.return_value = True
        start_date = Mock()

        result = Command.should_member_receive_reminder_mail(
            shift_user_data, start_date
        )

        self.assertFalse(result)
        mock_is_member_expected_to_do_shifts.assert_called_once_with(shift_user_data)
        mock_has_user_received_reminder_this_cycle.assert_called_once_with(
            shift_user_data, start_date
        )
        mock_is_member_registered_to_a_shift_this_cycle.assert_called_once_with(
            shift_user_data, start_date
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(Command, "has_user_received_reminder_this_cycle")
    @patch.object(Command, "is_member_registered_to_a_shift_this_cycle")
    def test_shouldMemberReceiveReminderMail_noReasonNotToSend_returnsTrue(
        self,
        mock_is_member_registered_to_a_shift_this_cycle: Mock,
        mock_has_user_received_reminder_this_cycle: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        shift_user_data = Mock()
        mock_is_member_expected_to_do_shifts.return_value = True
        mock_has_user_received_reminder_this_cycle.return_value = False
        mock_is_member_registered_to_a_shift_this_cycle.return_value = False
        start_date = Mock()

        result = Command.should_member_receive_reminder_mail(
            shift_user_data, start_date
        )

        self.assertTrue(result)
        mock_is_member_expected_to_do_shifts.assert_called_once_with(shift_user_data)
        mock_has_user_received_reminder_this_cycle.assert_called_once_with(
            shift_user_data, start_date
        )
        mock_is_member_registered_to_a_shift_this_cycle.assert_called_once_with(
            shift_user_data, start_date
        )

    def test_hasUserReceivedReminderThisCycle_noLogEntryForThisCycle_returnsFalse(self):
        tapir_user = TapirUserFactory.create()
        cycle_start_date = self.NOW.date()
        date_before_the_cycle = cycle_start_date - datetime.timedelta(days=1)
        date_after_the_cycle = cycle_start_date + datetime.timedelta(days=30)
        for date in [date_before_the_cycle, date_after_the_cycle]:
            entry = EmailLogEntry.objects.create(
                email_id=FlyingMemberRegistrationReminderEmail.get_unique_id(),
                user=tapir_user,
            )
            entry.created_date = date
            entry.save()

        self.assertFalse(
            Command.has_user_received_reminder_this_cycle(
                tapir_user.shift_user_data, cycle_start_date
            )
        )

    def test_hasUserReceivedReminderThisCycle_logEntryExistsWithinCycle_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        cycle_start_date = self.NOW.date()

        entry = EmailLogEntry.objects.create(
            email_id=FlyingMemberRegistrationReminderEmail.get_unique_id(),
            user=tapir_user,
        )
        entry.created_date = cycle_start_date + datetime.timedelta(days=1)
        entry.save()

        self.assertTrue(
            Command.has_user_received_reminder_this_cycle(
                tapir_user.shift_user_data, cycle_start_date
            )
        )

    def test_isMemberRegisteredToAShiftThisCycle_noAttendanceExistsWithinCycle_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        cycle_start_date = self.NOW.date()
        date_before_the_cycle = cycle_start_date - datetime.timedelta(days=1)
        date_after_the_cycle = cycle_start_date + datetime.timedelta(days=30)
        for date in [date_before_the_cycle, date_after_the_cycle]:
            shift = ShiftFactory.create(start_time=date)
            ShiftAttendance.objects.create(
                user=tapir_user,
                slot=shift.slots.first(),
                state=ShiftAttendance.State.PENDING,
            )

        shift = ShiftFactory.create(
            start_time=cycle_start_date + datetime.timedelta(days=2)
        )
        ShiftAttendance.objects.create(
            user=tapir_user,
            slot=shift.slots.first(),
            state=ShiftAttendance.State.CANCELLED,
        )

        self.assertFalse(
            Command.is_member_registered_to_a_shift_this_cycle(
                tapir_user.shift_user_data, cycle_start_date
            )
        )

    def test_isMemberRegisteredToAShiftThisCycle_attendanceExistsWithinCycle_returnsTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        cycle_start_date = self.NOW.date()
        shift = ShiftFactory.create(
            start_time=cycle_start_date + datetime.timedelta(days=1)
        )
        ShiftAttendance.objects.create(user=tapir_user, slot=shift.slots.first())

        self.assertTrue(
            Command.is_member_registered_to_a_shift_this_cycle(
                tapir_user.shift_user_data, cycle_start_date
            )
        )

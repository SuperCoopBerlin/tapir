import datetime
from unittest.mock import patch, MagicMock, Mock

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftAttendanceMode,
    ShiftUserData,
    ShiftAccountEntry,
    Shift,
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftTemplate,
)
from tapir.shifts.services.frozen_status_service import FrozenStatusService
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestFrozenStatusService(TapirFactoryTestBase):
    def test_shouldFreezeMember_memberAlreadyFrozen_returnsFalse(self):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))

    @patch.object(FrozenStatusService, "_is_member_below_threshold_since_long_enough")
    def test_shouldFreezeMember_memberNotBelowThreshold_returnsFalse(
        self, mock_is_member_below_threshold_since_long_enough
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        mock_is_member_below_threshold_since_long_enough.return_value = False
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))
        mock_is_member_below_threshold_since_long_enough.assert_called_once_with(
            shift_user_data
        )

    @patch.object(
        FrozenStatusService,
        "_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account",
    )
    @patch.object(FrozenStatusService, "_is_member_below_threshold_since_long_enough")
    def test_shouldFreezeMember_memberRegisteredToEnoughShifts_returnsFalse(
        self,
        mock_is_member_below_threshold_since_long_enough,
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account,
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        mock_is_member_below_threshold_since_long_enough.return_value = True
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.return_value = (
            True
        )
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))
        mock_is_member_below_threshold_since_long_enough.assert_called_once_with(
            shift_user_data
        )
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.assert_called_once_with(
            shift_user_data
        )

    @patch.object(
        FrozenStatusService,
        "_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account",
    )
    @patch.object(FrozenStatusService, "_is_member_below_threshold_since_long_enough")
    def test_shouldFreezeMember_shouldGetFrozen_returnsTrue(
        self,
        mock_is_member_below_threshold_since_long_enough,
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account,
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        mock_is_member_below_threshold_since_long_enough.return_value = True
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.return_value = (
            False
        )
        self.assertTrue(FrozenStatusService.should_freeze_member(shift_user_data))
        mock_is_member_below_threshold_since_long_enough.assert_called_once_with(
            shift_user_data
        )
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.assert_called_once_with(
            shift_user_data
        )

    def test_isMemberBelowThresholdSinceLongEnough_memberIsAboveThreshold_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        self.assertEqual(0, tapir_user.shift_user_data.get_account_balance())
        self.assertFalse(
            FrozenStatusService._is_member_below_threshold_since_long_enough(
                tapir_user.shift_user_data
            )
        )

    def test_isMemberBelowThresholdSinceLongEnough_memberIsBelowThresholdSinceLessDaysThanThreshold_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-2,
            date=timezone.now() - datetime.timedelta(days=20),
        )
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-2,
            date=timezone.now() - datetime.timedelta(days=5),
        )
        self.assertFalse(
            FrozenStatusService._is_member_below_threshold_since_long_enough(
                tapir_user.shift_user_data
            )
        )

    def test_isMemberBelowThresholdSinceLongEnough_memberIsBelowThresholdSinceMoreDaysThanThreshold_returnsTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-2,
            date=timezone.now() - datetime.timedelta(days=20),
        )
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-2,
            date=timezone.now() - datetime.timedelta(days=15),
        )
        self.assertTrue(
            FrozenStatusService._is_member_below_threshold_since_long_enough(
                tapir_user.shift_user_data
            )
        )

    def test_isMemberRegisteredToEnoughShiftsToCompensateForNegativeShiftAccount_notEnoughShifts_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-4,
            date=timezone.now() - datetime.timedelta(days=20),
        )

        for weeks_in_the_future in [4, 6, 8, 10]:
            shift: Shift = ShiftFactory.create(
                start_time=timezone.now()
                + datetime.timedelta(weeks=weeks_in_the_future)
            )
            ShiftAttendance.objects.create(
                user=tapir_user,
                slot=shift.slots.first(),
            )

        self.assertFalse(
            FrozenStatusService._is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
                tapir_user.shift_user_data
            )
        )

    def test_isMemberRegisteredToEnoughShiftsToCompensateForNegativeShiftAccount_enoughShifts_returnsTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-4,
            date=timezone.now() - datetime.timedelta(days=20),
        )

        for weeks_in_the_future in [1, 2, 3, 4]:
            shift: Shift = ShiftFactory.create(
                start_time=timezone.now()
                + datetime.timedelta(weeks=weeks_in_the_future)
            )
            ShiftAttendance.objects.create(
                user=tapir_user,
                slot=shift.slots.first(),
            )

        self.assertTrue(
            FrozenStatusService._is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
                tapir_user.shift_user_data
            )
        )

    @patch("tapir.shifts.services.frozen_status_service.MemberFrozenEmail")
    @patch.object(FrozenStatusService, "_cancel_future_attendances_templates")
    @patch.object(FrozenStatusService, "_update_attendance_mode_and_create_log_entry")
    def test_freezeMemberAndSendMail(
        self,
        mock_update_attendance_mode_and_create_log_entry,
        mock_cancel_future_attendances_templates,
        mock_member_frozen_email_class,
    ):
        tapir_user = TapirUserFactory.create()
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        ShiftAttendanceTemplate.objects.create(
            slot_template=shift_template.slot_templates.first(), user=tapir_user
        )
        actor = TapirUser()

        FrozenStatusService.freeze_member_and_send_email(
            tapir_user.shift_user_data, actor
        )

        mock_update_attendance_mode_and_create_log_entry.assert_called_once_with(
            tapir_user.shift_user_data, actor, ShiftAttendanceMode.FROZEN
        )
        mock_cancel_future_attendances_templates.assert_called_once_with(
            tapir_user.shift_user_data
        )
        self.assertEqual(0, ShiftAttendanceTemplate.objects.all().count())
        mock_member_frozen_email_class.assert_called_once()
        mock_member_frozen_email_class.return_value.send_to_tapir_user.assert_called_once_with(
            actor=actor, recipient=tapir_user
        )

    @patch("tapir.shifts.services.frozen_status_service.UpdateShiftUserDataLogEntry")
    @patch("tapir.shifts.services.frozen_status_service.freeze_for_log")
    def test_updateAttendanceModeAndCreateLogEntry(
        self, mock_freeze_for_log, mock_update_shift_user_data_log_entry_class
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        shift_user_data.save = MagicMock()
        shift_user_data.user = TapirUser()
        actor = TapirUser()
        mock_freeze_for_log.side_effect = (
            lambda data: 1 if data.attendance_mode == ShiftAttendanceMode.FLYING else 2
        )

        FrozenStatusService._update_attendance_mode_and_create_log_entry(
            shift_user_data, actor, ShiftAttendanceMode.FROZEN
        )

        shift_user_data.save.assert_called_once()
        self.assertEqual(2, mock_freeze_for_log.call_count)
        mock_update_shift_user_data_log_entry_class.assert_called_once()
        mock_entry = mock_update_shift_user_data_log_entry_class.return_value
        mock_entry.populate.assert_called_once_with(
            old_frozen=1, new_frozen=2, tapir_user=shift_user_data.user, actor=actor
        )
        mock_entry.populate.return_value.save.assert_called_once()

    @patch("tapir.shifts.services.frozen_status_service.timezone.now")
    @patch(
        "tapir.shifts.services.frozen_status_service.ShiftAttendanceTemplate.objects.filter"
    )
    def test_cancelFutureAttendancesTemplates(self, mock_filter, mock_now):
        shift_user_data = ShiftUserData()
        shift_user_data.user = TapirUser()
        mock_attendance_templates = [Mock(), Mock()]
        mock_filter.return_value = mock_attendance_templates

        FrozenStatusService._cancel_future_attendances_templates(shift_user_data)

        mock_filter.assert_called_once_with(user=shift_user_data.user)
        for mock_attendance_template in mock_attendance_templates:
            mock_attendance_template.cancel_attendances.assert_called_once_with(
                mock_now.return_value
            )
            mock_attendance_template.delete.assert_called_once_with()

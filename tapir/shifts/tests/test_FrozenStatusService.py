import datetime
from unittest.mock import patch

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

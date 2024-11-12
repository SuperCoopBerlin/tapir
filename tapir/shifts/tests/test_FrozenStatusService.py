import datetime
from unittest.mock import patch, MagicMock, Mock

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.log.models import EmailLogEntry
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
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestFrozenStatusService(TapirFactoryTestBase):
    FREEZE_WARNING_EMAIL_ID = "tapir.shifts.freeze_warning"
    NOW = datetime.datetime(year=2020, month=1, day=30, hour=16, minute=37)

    def setUp(self) -> None:
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_shouldFreezeMember_memberAlreadyFrozen_returnsFalse(self):
        shift_user_data = ShiftUserData()
        shift_user_data.is_frozen = True
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    def test_shouldFreezeMember_memberIsNotExpectedToDoShifts_returnsFalse(
        self, mock_is_member_expected_to_do_shifts: Mock
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        mock_is_member_expected_to_do_shifts.return_value = False
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data, self.NOW
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(FrozenStatusService, "_is_member_below_threshold_since_long_enough")
    def test_shouldFreezeMember_memberNotBelowThreshold_returnsFalse(
        self,
        mock_is_member_below_threshold_since_long_enough: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        mock_is_member_expected_to_do_shifts.return_value = True
        mock_is_member_below_threshold_since_long_enough.return_value = False
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))
        mock_is_member_below_threshold_since_long_enough.assert_called_once_with(
            shift_user_data
        )
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data, self.NOW
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(
        FrozenStatusService,
        "_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account",
    )
    @patch.object(FrozenStatusService, "_is_member_below_threshold_since_long_enough")
    def test_shouldFreezeMember_memberRegisteredToEnoughShifts_returnsFalse(
        self,
        mock_is_member_below_threshold_since_long_enough: Mock,
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        mock_is_member_below_threshold_since_long_enough.return_value = True
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.return_value = (
            True
        )
        mock_is_member_expected_to_do_shifts.return_value = True
        self.assertFalse(FrozenStatusService.should_freeze_member(shift_user_data))
        mock_is_member_below_threshold_since_long_enough.assert_called_once_with(
            shift_user_data
        )
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.assert_called_once_with(
            shift_user_data
        )
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data, self.NOW
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(
        FrozenStatusService,
        "_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account",
    )
    @patch.object(FrozenStatusService, "_is_member_below_threshold_since_long_enough")
    def test_shouldFreezeMember_shouldGetFrozen_returnsTrue(
        self,
        mock_is_member_below_threshold_since_long_enough: Mock,
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
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
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data, self.NOW
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

    def test_isMemberRegisteredToEnoughShiftsToCompensateForNegativeShiftAccount_enoughShiftsIncludingSomeInThePast_returnsTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        ShiftAccountEntry.objects.create(
            user=tapir_user,
            value=-4,
            date=timezone.now() - datetime.timedelta(days=20),
        )

        for weeks_in_the_future in [-2, -1, 1, 2]:
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
        mock_update_attendance_mode_and_create_log_entry: Mock,
        mock_cancel_future_attendances_templates: Mock,
        mock_member_frozen_email_class: Mock,
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
        self,
        mock_freeze_for_log: Mock,
        mock_update_shift_user_data_log_entry_class: Mock,
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        shift_user_data.save = MagicMock()
        shift_user_data.user = TapirUser()
        actor = TapirUser()
        mock_freeze_for_log.side_effect = lambda data: (
            1 if data.attendance_mode == ShiftAttendanceMode.FLYING else 2
        )

        FrozenStatusService._update_attendance_mode_and_create_log_entry(
            shift_user_data, actor, ShiftAttendanceMode.FROZEN
        )

        self.assertEqual(ShiftAttendanceMode.FROZEN, shift_user_data.attendance_mode)
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
    def test_cancelFutureAttendancesTemplates(self, mock_filter: Mock, mock_now: Mock):
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

    def test_shouldSendFreezeWarning_balanceAboveThreshold_returnsFalse(self):
        shift_user_data = Mock()
        shift_user_data.get_account_balance.return_value = -3

        self.assertFalse(
            FrozenStatusService.should_send_freeze_warning(shift_user_data)
        )
        shift_user_data.get_account_balance.assert_called_once()

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    def test_shouldSendFreezeWarning_memberNotExpectedToDoShifts_returnsFalse(
        self, mock_is_member_expected_to_do_shifts: Mock
    ):
        shift_user_data = Mock()
        shift_user_data.get_account_balance.return_value = -6
        mock_is_member_expected_to_do_shifts.return_value = False
        self.assertFalse(
            FrozenStatusService.should_send_freeze_warning(shift_user_data)
        )
        shift_user_data.get_account_balance.assert_called_once()
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data, self.NOW
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(EmailLogEntry, "objects")
    def test_shouldSendFreezeWarning_warningNeverSent_returnsTrue(
        self, mock_email_log_queryset: Mock, mock_is_member_expected_to_do_shifts: Mock
    ):
        mock_shift_user_data = Mock()
        mock_shift_user_data.user = Mock()
        mock_shift_user_data.get_account_balance.return_value = -5
        mock_is_member_expected_to_do_shifts.return_value = True
        mock_email_log_queryset.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        self.assertTrue(
            FrozenStatusService.should_send_freeze_warning(mock_shift_user_data)
        )

        mock_shift_user_data.get_account_balance.assert_called_once()
        mock_email_log_queryset.filter.assert_called_once_with(
            email_id=self.FREEZE_WARNING_EMAIL_ID, user=mock_shift_user_data.user
        )
        mock_order_by = mock_email_log_queryset.filter.return_value.order_by
        mock_order_by.assert_called_once_with("-created_date")
        mock_first = mock_order_by.return_value.first
        mock_first.assert_called_once_with()
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            mock_shift_user_data, self.NOW
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(EmailLogEntry, "objects")
    def test_shouldSendFreezeWarning_warningSentLongAgo_returnsTrue(
        self,
        mock_email_log_queryset: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        mock_shift_user_data = Mock()
        mock_shift_user_data.user = Mock()
        mock_shift_user_data.get_account_balance.return_value = -5
        mock_last_warning = Mock()
        mock_last_warning.created_date = datetime.datetime(year=2020, month=1, day=10)
        mock_email_log_queryset.filter.return_value.order_by.return_value.first.return_value = (
            mock_last_warning
        )
        mock_is_member_expected_to_do_shifts.return_value = True

        self.assertTrue(
            FrozenStatusService.should_send_freeze_warning(mock_shift_user_data)
        )

        mock_shift_user_data.get_account_balance.assert_called_once()
        mock_email_log_queryset.filter.assert_called_once_with(
            email_id=self.FREEZE_WARNING_EMAIL_ID, user=mock_shift_user_data.user
        )
        mock_order_by = mock_email_log_queryset.filter.return_value.order_by
        mock_order_by.assert_called_once_with("-created_date")
        mock_first = mock_order_by.return_value.first
        mock_first.assert_called_once_with()
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            mock_shift_user_data, self.NOW
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    @patch.object(EmailLogEntry, "objects")
    def test_shouldSendFreezeWarning_warningSentInTheLast10Days_returnsFalse(
        self,
        mock_email_log_queryset: Mock,
        mock_is_member_expected_to_do_shifts: Mock,
    ):
        mock_shift_user_data = Mock()
        mock_shift_user_data.user = Mock()
        mock_shift_user_data.get_account_balance.return_value = -5
        mock_last_warning = Mock()
        mock_last_warning.created_date = datetime.datetime(year=2020, month=1, day=25)
        mock_email_log_queryset.filter.return_value.order_by.return_value.first.return_value = (
            mock_last_warning
        )
        mock_is_member_expected_to_do_shifts.return_value = True

        self.assertFalse(
            FrozenStatusService.should_send_freeze_warning(mock_shift_user_data)
        )

        mock_shift_user_data.get_account_balance.assert_called_once()
        mock_email_log_queryset.filter.assert_called_once_with(
            email_id=self.FREEZE_WARNING_EMAIL_ID, user=mock_shift_user_data.user
        )
        mock_order_by = mock_email_log_queryset.filter.return_value.order_by
        mock_order_by.assert_called_once_with("-created_date")
        mock_first = mock_order_by.return_value.first
        mock_first.assert_called_once_with()
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            mock_shift_user_data, self.NOW
        )

    @patch("tapir.shifts.services.frozen_status_service.FreezeWarningEmail")
    def test_send_freeze_warning_email(self, mock_freeze_warning_email_class: Mock):
        shift_user_data = ShiftUserData()
        shift_user_data.user = TapirUser()

        FrozenStatusService.send_freeze_warning_email(shift_user_data)

        mock_freeze_warning_email_class.assert_called_once_with(shift_user_data)
        mock_send_to_tapir_user = (
            mock_freeze_warning_email_class.return_value.send_to_tapir_user
        )
        mock_send_to_tapir_user.assert_called_once_with(
            actor=None, recipient=shift_user_data.user
        )

    def test_shouldUnfreezeMember_memberIsNotFrozen_returnsFalse(self):
        shift_user_data = ShiftUserData()
        shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR

        self.assertFalse(FrozenStatusService.should_unfreeze_member(shift_user_data))

    def test_shouldUnfreezeMember_memberIsInactive_returnsFalse(self):
        shift_user_data = Mock()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        shift_user_data.get_account_balance.return_value = 10
        shift_user_data.user.share_owner.is_active.return_value = False

        self.assertFalse(FrozenStatusService.should_unfreeze_member(shift_user_data))

        shift_user_data.user.share_owner.is_active.assert_called_once_with()

    def test_shouldUnfreezeMember_memberBalanceIsAboveThreshold_returnsTrue(self):
        shift_user_data = Mock()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        shift_user_data.get_account_balance.return_value = -3
        shift_user_data.user.share_owner.is_active.return_value = True

        self.assertTrue(FrozenStatusService.should_unfreeze_member(shift_user_data))

        shift_user_data.user.share_owner.is_active.assert_called_once_with()
        shift_user_data.get_account_balance.assert_called_once_with()

    @patch.object(
        FrozenStatusService,
        "_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account",
    )
    def test_shouldUnfreezeMember_memberRegisteredToEnoughShifts_returnsTrue(
        self,
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account: Mock,
    ):
        shift_user_data = Mock()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        shift_user_data.get_account_balance.return_value = -5
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.return_value = (
            True
        )
        shift_user_data.user.share_owner.is_active.return_value = True

        self.assertTrue(FrozenStatusService.should_unfreeze_member(shift_user_data))

        shift_user_data.user.share_owner.is_active.assert_called_once_with()
        shift_user_data.get_account_balance.assert_called_once_with()
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.assert_called_once_with(
            shift_user_data
        )

    @patch.object(
        FrozenStatusService,
        "_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account",
    )
    def test_shouldUnfreezeMember_memberNotRegisteredToEnoughShifts_returnsFalse(
        self,
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account: Mock,
    ):
        shift_user_data = Mock()
        shift_user_data.attendance_mode = ShiftAttendanceMode.FROZEN
        shift_user_data.get_account_balance.return_value = -5
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.return_value = (
            False
        )
        shift_user_data.user.share_owner.is_active.return_value = True

        self.assertFalse(FrozenStatusService.should_unfreeze_member(shift_user_data))

        shift_user_data.user.share_owner.is_active.assert_called_once_with()
        shift_user_data.get_account_balance.assert_called_once_with()
        mock_is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account.assert_called_once_with(
            shift_user_data
        )

    @patch("tapir.shifts.services.frozen_status_service.UnfreezeNotificationEmail")
    @patch.object(
        FrozenStatusService,
        "_get_last_attendance_mode_before_frozen",
    )
    @patch.object(
        FrozenStatusService,
        "_update_attendance_mode_and_create_log_entry",
    )
    def test_unfreezeAndSendNotificationEmail(
        self,
        mock_update_attendance_mode_and_create_log_entry: Mock,
        mock_get_last_attendance_mode_before_frozen: Mock,
        mock_unfreeze_notification_email_class: Mock,
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.user = TapirUser()
        actor = TapirUser()
        mock_get_last_attendance_mode_before_frozen.return_value = (
            ShiftAttendanceMode.REGULAR
        )

        FrozenStatusService.unfreeze_and_send_notification_email(shift_user_data, actor)

        mock_update_attendance_mode_and_create_log_entry.assert_called_once_with(
            shift_user_data=shift_user_data,
            actor=actor,
            attendance_mode=ShiftAttendanceMode.REGULAR,
        )
        mock_unfreeze_notification_email_class.assert_called_once_with()
        mock_email = mock_unfreeze_notification_email_class.return_value
        mock_email.send_to_tapir_user.assert_called_once_with(
            actor=actor, recipient=shift_user_data.user
        )

    @patch(
        "tapir.shifts.services.frozen_status_service.UpdateShiftUserDataLogEntry.objects.filter"
    )
    def test_getLastAttendanceModeBeforeFrozen_noLogEntryFound_returnsFlying(
        self, mock_filter: Mock
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.user = TapirUser()
        mock_order_by = mock_filter.return_value.order_by
        mock_first = mock_order_by.return_value.first
        mock_first.return_value = None

        self.assertEqual(
            ShiftAttendanceMode.FLYING,
            FrozenStatusService._get_last_attendance_mode_before_frozen(
                shift_user_data
            ),
        )

        mock_filter.assert_called_once_with(
            new_values__attendance_mode=ShiftAttendanceMode.FROZEN,
            user=shift_user_data.user,
        )
        mock_order_by.assert_called_once_with("-created_date")
        mock_first.assert_called_once_with()

    @patch(
        "tapir.shifts.services.frozen_status_service.UpdateShiftUserDataLogEntry.objects.filter"
    )
    def test_getLastAttendanceModeBeforeFrozen_default_returnsLastMode(
        self, mock_filter: Mock
    ):
        shift_user_data = ShiftUserData()
        shift_user_data.user = TapirUser()
        mock_order_by = mock_filter.return_value.order_by
        mock_first = mock_order_by.return_value.first
        mock_first.return_value = Mock()
        mock_first.return_value.old_values = dict()
        mock_first.return_value.old_values["attendance_mode"] = (
            ShiftAttendanceMode.REGULAR
        )

        self.assertEqual(
            ShiftAttendanceMode.REGULAR,
            FrozenStatusService._get_last_attendance_mode_before_frozen(
                shift_user_data
            ),
        )

        mock_filter.assert_called_once_with(
            new_values__attendance_mode=ShiftAttendanceMode.FROZEN,
            user=shift_user_data.user,
        )
        mock_order_by.assert_called_once_with("-created_date")
        mock_first.assert_called_once_with()

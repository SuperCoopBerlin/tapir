from unittest.mock import patch, Mock

from django.core.management import call_command

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.config import FEATURE_FLAG_NAME_FROZEN_MEMBERS
from tapir.shifts.services.frozen_status_service import FrozenStatusService
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestRunFreezeChecks(TapirFactoryTestBase):
    def setUp(self) -> None:
        patcher = patch("tapir.core.models.FeatureFlag.get_flag_value")
        self.mock_get_flag_value = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_get_flag_value.side_effect = (
            lambda flag_name: flag_name == FEATURE_FLAG_NAME_FROZEN_MEMBERS
        )

    @patch.object(FrozenStatusService, "should_freeze_member")
    @patch.object(FrozenStatusService, "should_send_freeze_warning")
    @patch.object(FrozenStatusService, "should_unfreeze_member")
    def test_featureFlagDisabled_nothingGetsCalled(
        self,
        mock_should_freeze_member: Mock,
        mock_should_send_freeze_warning: Mock,
        mock_should_unfreeze_member: Mock,
    ):
        TapirUserFactory.create()
        self.mock_get_flag_value.side_effect = lambda _: False
        call_command("run_freeze_checks")
        mock_should_freeze_member.assert_not_called()
        mock_should_send_freeze_warning.assert_not_called()
        mock_should_unfreeze_member.assert_not_called()

    @patch.object(FrozenStatusService, "should_freeze_member")
    def test_should_freeze_member_gets_called_once_per_member(
        self, mock_should_freeze_member
    ):
        tapir_user_1 = TapirUserFactory.create()
        tapir_user_2 = TapirUserFactory.create()
        call_command("run_freeze_checks")
        self.assertEqual(2, mock_should_freeze_member.call_count)
        mock_should_freeze_member.has_calls([tapir_user_1, tapir_user_2])

    @patch.object(FrozenStatusService, "freeze_member_and_send_email")
    @patch.object(FrozenStatusService, "should_freeze_member")
    def test_member_that_should_be_frozen_gets_frozen(
        self, mock_should_freeze_member, mock_freeze_member_and_send_email
    ):
        _ = TapirUserFactory.create()
        tapir_user_2 = TapirUserFactory.create()
        mock_should_freeze_member.side_effect = (
            lambda shift_user_data: shift_user_data == tapir_user_2.shift_user_data
        )
        call_command("run_freeze_checks")
        self.assertEqual(1, mock_freeze_member_and_send_email.call_count)
        mock_freeze_member_and_send_email.assert_called_once_with(
            tapir_user_2.shift_user_data, actor=None
        )

    @patch.object(FrozenStatusService, "should_freeze_member")
    @patch.object(FrozenStatusService, "should_send_freeze_warning")
    def test_only_relevant_members_get_checked_for_freeze_warning(
        self, mock_should_send_freeze_warning, mock_should_freeze_member
    ):
        tapir_user_1 = TapirUserFactory.create()
        tapir_user_2 = TapirUserFactory.create()
        mock_should_freeze_member.side_effect = (
            lambda shift_user_data: shift_user_data == tapir_user_1.shift_user_data
        )
        call_command("run_freeze_checks")
        self.assertEqual(1, mock_should_send_freeze_warning.call_count)
        mock_should_send_freeze_warning.assert_called_once_with(
            tapir_user_2.shift_user_data
        )

    @patch.object(FrozenStatusService, "should_freeze_member")
    @patch.object(FrozenStatusService, "should_send_freeze_warning")
    @patch.object(FrozenStatusService, "send_freeze_warning_email")
    def test_member_that_should_receive_freeze_warning_receives_freeze_warning(
        self,
        mock_send_freeze_warning_email,
        mock_should_send_freeze_warning,
        mock_should_freeze_member,
    ):
        tapir_user_1 = TapirUserFactory.create()
        _ = TapirUserFactory.create()
        mock_should_freeze_member.return_value = False
        mock_should_send_freeze_warning.side_effect = (
            lambda shift_user_data: shift_user_data == tapir_user_1.shift_user_data
        )
        call_command("run_freeze_checks")
        self.assertEqual(1, mock_send_freeze_warning_email.call_count)
        mock_send_freeze_warning_email.assert_called_once_with(
            tapir_user_1.shift_user_data
        )

    @patch.object(FrozenStatusService, "should_freeze_member")
    @patch.object(FrozenStatusService, "should_send_freeze_warning")
    @patch.object(FrozenStatusService, "send_freeze_warning_email")
    def test_member_that_should_get_frozen_does_not_get_warning(
        self,
        mock_send_freeze_warning_email,
        mock_should_send_freeze_warning,
        mock_should_freeze_member,
    ):
        TapirUserFactory.create()
        mock_should_freeze_member.return_value = True
        call_command("run_freeze_checks")
        mock_should_send_freeze_warning.assert_not_called()
        mock_send_freeze_warning_email.assert_not_called()

    @patch.object(FrozenStatusService, "should_freeze_member")
    @patch.object(FrozenStatusService, "should_send_freeze_warning")
    @patch.object(FrozenStatusService, "should_unfreeze_member")
    def test_only_relevant_members_get_checked_for_unfreeze(
        self,
        mock_should_unfreeze_member,
        mock_should_send_freeze_warning,
        mock_should_freeze_member,
    ):
        tapir_user_1 = TapirUserFactory.create()
        tapir_user_2 = TapirUserFactory.create()
        tapir_user_3 = TapirUserFactory.create()
        mock_should_freeze_member.side_effect = (
            lambda shift_user_data: shift_user_data == tapir_user_1.shift_user_data
        )
        mock_should_send_freeze_warning.side_effect = (
            lambda shift_user_data: shift_user_data == tapir_user_2.shift_user_data
        )
        call_command("run_freeze_checks")
        self.assertEqual(1, mock_should_unfreeze_member.call_count)
        mock_should_unfreeze_member.assert_called_once_with(
            tapir_user_3.shift_user_data
        )

    @patch.object(FrozenStatusService, "should_freeze_member")
    @patch.object(FrozenStatusService, "should_send_freeze_warning")
    @patch.object(FrozenStatusService, "should_unfreeze_member")
    @patch.object(FrozenStatusService, "unfreeze_and_send_notification_email")
    def test_member_who_should_get_unfrozen_gets_unfrozen(
        self,
        mock_unfreeze_and_send_notification_email,
        mock_should_unfreeze_member,
        mock_should_send_freeze_warning,
        mock_should_freeze_member,
    ):
        _ = TapirUserFactory.create()
        tapir_user_2 = TapirUserFactory.create()
        mock_should_freeze_member.return_value = False
        mock_should_send_freeze_warning.return_value = False
        mock_should_unfreeze_member.side_effect = (
            lambda shift_user_data: shift_user_data == tapir_user_2.shift_user_data
        )
        call_command("run_freeze_checks")
        self.assertEqual(1, mock_unfreeze_and_send_notification_email.call_count)
        mock_unfreeze_and_send_notification_email.assert_called_once_with(
            tapir_user_2.shift_user_data
        )

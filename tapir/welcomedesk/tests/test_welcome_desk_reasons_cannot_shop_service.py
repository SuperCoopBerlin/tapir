import datetime
from unittest.mock import patch, Mock

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.services.InvestingStatusService import InvestingStatusService
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.welcomedesk.services.welcome_desk_reasons_cannot_shop_service import (
    WelcomeDeskReasonsCannotShopService,
)


class TestWelcomeDeskReasonsCannotShopService(TapirFactoryTestBase):

    def test_shouldShowNoAccountReason_memberHasNoAccount_returnsTrue(
        self,
    ):
        share_owner = ShareOwnerFactory.build()
        self.assertTrue(
            WelcomeDeskReasonsCannotShopService.should_show_no_account_reason(
                share_owner
            )
        )

    def test_shouldShowNoAccountReason_memberHasAnAccount_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.build()
        self.assertFalse(
            WelcomeDeskReasonsCannotShopService.should_show_no_account_reason(
                tapir_user.share_owner
            )
        )

    @patch.object(InvestingStatusService, "is_investing")
    def test_shouldShowInvestingReason_memberIsInvesting_returnsTrue(
        self, mock_is_investing: Mock
    ):
        share_owner = ShareOwnerFactory.build()
        reference_time = datetime.datetime.now()
        mock_is_investing.return_value = True

        self.assertTrue(
            WelcomeDeskReasonsCannotShopService.should_show_investing_reason(
                share_owner, reference_time
            )
        )
        mock_is_investing.assert_called_once_with(share_owner, reference_time)

    @patch.object(InvestingStatusService, "is_investing")
    def test_shouldShowInvestingReason_memberIsNotInvesting_returnsFalse(
        self, mock_is_investing: Mock
    ):
        share_owner = ShareOwnerFactory.build()
        reference_time = datetime.datetime.now()
        mock_is_investing.return_value = False

        self.assertFalse(
            WelcomeDeskReasonsCannotShopService.should_show_investing_reason(
                share_owner, reference_time
            )
        )
        mock_is_investing.assert_called_once_with(share_owner, reference_time)

    @patch.object(ShiftAttendanceModeService, "is_frozen_at_date")
    def test_shouldShowFrozenReason_memberIsFrozen_returnsTrue(
        self, mock_is_frozen_at_date: Mock
    ):
        share_owner = Mock()
        shift_user_data = Mock()
        share_owner.user.shift_user_data = shift_user_data
        reference_date = datetime.datetime.today()
        mock_is_frozen_at_date.return_value = True

        self.assertTrue(
            WelcomeDeskReasonsCannotShopService.should_show_frozen_reason(
                share_owner, reference_date
            )
        )
        mock_is_frozen_at_date.assert_called_once_with(shift_user_data, reference_date)

    @patch.object(ShiftAttendanceModeService, "is_frozen_at_date")
    def test_shouldShowFrozenReason_memberIsNotFrozen_returnsFalse(
        self, mock_is_frozen_at_date: Mock
    ):
        share_owner = Mock()
        shift_user_data = Mock()
        share_owner.user.shift_user_data = shift_user_data
        reference_date = datetime.datetime.today()
        mock_is_frozen_at_date.return_value = False

        self.assertFalse(
            WelcomeDeskReasonsCannotShopService.should_show_frozen_reason(
                share_owner, reference_date
            )
        )
        mock_is_frozen_at_date.assert_called_once_with(shift_user_data, reference_date)

    @patch.object(MembershipPauseService, "has_active_pause")
    def test_shouldShowPausedReason_memberIsPaused_returnsTrue(
        self, mock_has_active_pause: Mock
    ):
        share_owner = ShareOwnerFactory.build()
        reference_date = datetime.datetime.today()
        mock_has_active_pause.return_value = True

        self.assertTrue(
            WelcomeDeskReasonsCannotShopService.should_show_paused_reason(
                share_owner, reference_date
            )
        )
        mock_has_active_pause.assert_called_once_with(share_owner, reference_date)

    @patch.object(MembershipPauseService, "has_active_pause")
    def test_shouldShowPausedReason_memberIsNotPaused_returnsFalse(
        self, mock_has_active_pause: Mock
    ):
        share_owner = ShareOwnerFactory.build()
        reference_date = datetime.datetime.today()
        mock_has_active_pause.return_value = False

        self.assertFalse(
            WelcomeDeskReasonsCannotShopService.should_show_paused_reason(
                share_owner, reference_date
            )
        )
        mock_has_active_pause.assert_called_once_with(share_owner, reference_date)

    @patch.object(WelcomeDeskReasonsCannotShopService, "should_show_no_account_reason")
    @patch.object(WelcomeDeskReasonsCannotShopService, "should_show_investing_reason")
    @patch.object(WelcomeDeskReasonsCannotShopService, "should_show_frozen_reason")
    @patch.object(WelcomeDeskReasonsCannotShopService, "should_show_paused_reason")
    def test_buildReasonsWhyThisMemberCannotShop_default_callsAllChecks(self, *mocks):
        share_owner = ShareOwnerFactory.build()
        request_user = TapirUserFactory.create()
        reference_time = datetime.datetime.now()
        reference_date = datetime.datetime.today()
        for mock in mocks:
            mock.return_value = True

        reasons = WelcomeDeskReasonsCannotShopService.build_reasons_why_this_member_cannot_shop(
            share_owner, request_user, reference_time, reference_date
        )

        self.assertEqual(4, len(reasons))
        for mock in mocks:
            mock.assert_called_once_with(
                share_owner=share_owner,
                reference_time=reference_time,
                reference_date=reference_date,
            )

from unittest.mock import patch, Mock

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.welcomedesk.services.welcome_desk_warnings_service import (
    WelcomeDeskWarningsService,
)


class TestWelcomeDeskWarningsService(TapirFactoryTestBase):

    def test_shouldShowWelcomeSessionWarning_memberWentToWelcomeSession_returnsFalse(
        self,
    ):
        share_owner = ShareOwnerFactory.build(attended_welcome_session=True)
        self.assertFalse(
            WelcomeDeskWarningsService.should_show_welcome_session_warning(share_owner)
        )

    def test_shouldShowWelcomeSessionWarning_memberDidntGoToWelcomeSession_returnsTrue(
        self,
    ):
        share_owner = ShareOwnerFactory.build(attended_welcome_session=False)
        self.assertTrue(
            WelcomeDeskWarningsService.should_show_welcome_session_warning(share_owner)
        )

    @patch.object(WelcomeDeskWarningsService, "should_show_welcome_session_warning")
    def test_buildWarnings_default_callsAllChecks(
        self,
        mock_should_show_welcome_session_warning: Mock,
    ):
        share_owner = ShareOwnerFactory.build()
        request_user = TapirUserFactory.create()
        mock_should_show_welcome_session_warning.return_value = True

        warnings = WelcomeDeskWarningsService.build_warnings(share_owner, request_user)

        self.assertEqual(1, len(warnings))
        mock_should_show_welcome_session_warning.assert_called_once_with(
            share_owner=share_owner
        )

from unittest.mock import Mock, patch

from django.core.exceptions import BadRequest
from django.test import SimpleTestCase

from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.services.coops_pt_login_manager import CoopsPtLoginManager


class TestsDoRemoteLogin(SimpleTestCase):
    def test_doRemoteLogin_noEmailAndNoUsernameSent_raisesBadRequest(self):
        kwargs = {}
        request = Mock()

        with self.assertRaises(BadRequest):
            CoopsPtAuthBackend().authenticate(request=request, **kwargs)

    @patch.object(CoopsPtLoginManager, "remote_login", autospec=True)
    def test_doRemoteLogin_onlyUsernameSent_usesUsernameAsEmail(
        self, mock_remote_login: Mock
    ):
        kwargs = {"username": "test_username", "password": "pw"}
        request = Mock()
        mock_remote_login.return_value = False, "", ""

        CoopsPtAuthBackend().authenticate(request=request, **kwargs)

        mock_remote_login.assert_called_once_with(email="test_username", password="pw")

    @patch.object(CoopsPtLoginManager, "remote_login", autospec=True)
    def test_doRemoteLogin_bothUsernameAndEmailSent_usesEmail(
        self, mock_remote_login: Mock
    ):
        kwargs = {"email": "test_email", "username": "test_username", "password": "pw"}
        request = Mock()
        mock_remote_login.return_value = False, "", ""

        CoopsPtAuthBackend().authenticate(request=request, **kwargs)

        mock_remote_login.assert_called_once_with(email="test_email", password="pw")

    def test_doRemoteLogin_noPasswordSent_raisesBadRequest(self):
        kwargs = {"email": "test_email"}
        request = Mock()

        with self.assertRaises(BadRequest):
            CoopsPtAuthBackend().authenticate(request=request, **kwargs)

    @patch("tapir.rizoma.coops_pt_auth_backend.messages", autospec=True)
    @patch.object(CoopsPtLoginManager, "remote_login", autospec=True)
    def test_doRemoteLogin_remoteLoginFails_addDjangoMessageAndReturnsNone(
        self, mock_remote_login: Mock, mock_messages: Mock
    ):
        kwargs = {"email": "test_email", "password": "pw"}
        request = Mock()
        mock_remote_login.return_value = False, "", ""

        result = CoopsPtAuthBackend().authenticate(request=request, **kwargs)

        self.assertIsNone(result)
        mock_remote_login.assert_called_once_with(email="test_email", password="pw")
        mock_messages.info.assert_called_once_with(
            request, "Invalid username or password"
        )

    @patch("tapir.rizoma.coops_pt_auth_backend.messages", autospec=True)
    @patch.object(CoopsPtLoginManager, "remote_login", autospec=True)
    def test_doRemoteLogin_remoteLoginReturnsInvalidValues_addDjangoMessageAndReturnsNone(
        self, mock_remote_login: Mock, mock_messages: Mock
    ):
        kwargs = {"email": "test_email", "password": "pw"}
        request = Mock()
        mock_remote_login.return_value = True, None, None

        result = CoopsPtAuthBackend().authenticate(request=request, **kwargs)

        self.assertIsNone(result)
        mock_remote_login.assert_called_once_with(email="test_email", password="pw")
        mock_messages.error.assert_called_once_with(
            request, "Login system error, please try again later or contact an admin."
        )

from unittest.mock import patch, Mock, call

from django.test import SimpleTestCase

from tapir.rizoma.services.coops_pt_login_manager import CoopsPtLoginManager
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler


class TestRemoteLogin(SimpleTestCase):
    @patch.object(CoopsPtRequestHandler, "post", autospec=True)
    def test_remoteLogin_requestFails_returnsNone(self, mock_post: Mock):
        response = Mock()
        response.status_code = 500
        mock_post.return_value = response

        result = CoopsPtLoginManager.remote_login(
            email="test_email", password="test_password"
        )

        self.assertEqual((False, None, None), result)
        mock_post.assert_called_once_with(
            url="auth", data={"email": "test_email", "password": "test_password"}
        )

    @patch.object(CoopsPtLoginManager, "validate_and_decode_token", autospec=True)
    @patch.object(CoopsPtRequestHandler, "post", autospec=True)
    def test_remoteLogin_requestSucceeds_validatesAndReturnsTokens(
        self, mock_post: Mock, mock_validate_and_decode_token: Mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "access": "encoded_access_token",
            "refresh": "encoded_refresh_token",
        }
        mock_post.return_value = response

        result = CoopsPtLoginManager.remote_login(
            email="test_email", password="test_password"
        )

        self.assertEqual(
            (True, "encoded_access_token", "encoded_refresh_token"), result
        )
        mock_post.assert_called_once_with(
            url="auth", data={"email": "test_email", "password": "test_password"}
        )
        self.assertEqual(2, mock_validate_and_decode_token.call_count)
        mock_validate_and_decode_token.assert_has_calls(
            [call("encoded_access_token"), call("encoded_refresh_token")],
            any_order=True,
        )

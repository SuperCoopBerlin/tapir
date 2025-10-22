from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.exceptions import CoopsPtRequestException
from tapir.rizoma.services.coops_pt_login_manager import CoopsPtLoginManager
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler


class TestAuthenticate(SimpleTestCase):
    @patch.object(CoopsPtAuthBackend, "do_remote_login", autospec=True)
    def test_authenticate_remoteLoginFails_returnsNone(
        self, mock_do_remote_login: Mock
    ):
        request = Mock()
        kwargs = {}
        mock_do_remote_login.return_value = None

        result = CoopsPtAuthBackend().authenticate(request, **kwargs)

        self.assertIsNone(result)
        mock_do_remote_login.assert_called_once_with(request, **kwargs)

    @patch.object(
        CoopsPtAuthBackend, "get_existing_user_and_update_admin_status", autospec=True
    )
    @patch.object(
        CoopsPtLoginManager, "get_external_user_id_from_access_token", autospec=True
    )
    @patch.object(CoopsPtAuthBackend, "do_remote_login", autospec=True)
    def test_authenticate_userWithExternalIdExists_returnsUser(
        self,
        mock_do_remote_login: Mock,
        mock_get_external_user_id_from_access_token: Mock,
        mock_get_existing_user_and_update_admin_status: Mock,
    ):
        request = Mock()
        kwargs = {}
        mock_do_remote_login.return_value = "test_access_token"
        mock_get_external_user_id_from_access_token.return_value = (
            "test_external_user_id"
        )
        user = TapirUserFactory.build()
        mock_get_existing_user_and_update_admin_status.return_value = user

        result = CoopsPtAuthBackend().authenticate(request, **kwargs)

        self.assertEqual(user, result)
        mock_do_remote_login.assert_called_once_with(request, **kwargs)
        mock_get_external_user_id_from_access_token.assert_called_once_with(
            "test_access_token"
        )
        mock_get_existing_user_and_update_admin_status.assert_called_once_with(
            external_user_id="test_external_user_id", access_token="test_access_token"
        )

    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    @patch.object(
        CoopsPtAuthBackend, "get_existing_user_and_update_admin_status", autospec=True
    )
    @patch.object(
        CoopsPtLoginManager, "get_external_user_id_from_access_token", autospec=True
    )
    @patch.object(CoopsPtAuthBackend, "do_remote_login", autospec=True)
    def test_authenticate_coopsPtRequestFails_raisesException(
        self,
        mock_do_remote_login: Mock,
        mock_get_external_user_id_from_access_token: Mock,
        mock_get_existing_user_and_update_admin_status: Mock,
        mock_request_get: Mock,
    ):
        request = Mock()
        kwargs = {}
        mock_do_remote_login.return_value = "test_access_token"
        mock_get_external_user_id_from_access_token.return_value = (
            "test_external_user_id"
        )
        mock_get_existing_user_and_update_admin_status.return_value = None
        response = Mock()
        response.status_code = 500
        mock_request_get.return_value = response

        with self.assertRaises(CoopsPtRequestException):
            CoopsPtAuthBackend().authenticate(request, **kwargs)

        mock_do_remote_login.assert_called_once_with(request, **kwargs)
        mock_get_external_user_id_from_access_token.assert_called_once_with(
            "test_access_token"
        )
        mock_get_existing_user_and_update_admin_status.assert_called_once_with(
            external_user_id="test_external_user_id", access_token="test_access_token"
        )
        mock_request_get.assert_called_once_with(
            "users/test_external_user_id", **kwargs
        )

    @patch.object(
        CoopsPtAuthBackend,
        "check_for_inactive_user_with_same_email_address",
        autospec=True,
    )
    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    @patch.object(
        CoopsPtAuthBackend, "get_existing_user_and_update_admin_status", autospec=True
    )
    @patch.object(
        CoopsPtLoginManager, "get_external_user_id_from_access_token", autospec=True
    )
    @patch.object(CoopsPtAuthBackend, "do_remote_login", autospec=True)
    def test_authenticate_inactiveUserWithSameEmailExists_returnsUser(
        self,
        mock_do_remote_login: Mock,
        mock_get_external_user_id_from_access_token: Mock,
        mock_get_existing_user_and_update_admin_status: Mock,
        mock_request_get: Mock,
        mock_check_for_inactive_user_with_same_email_address: Mock,
    ):
        request = Mock()
        kwargs = {}
        mock_do_remote_login.return_value = "test_access_token"
        mock_get_external_user_id_from_access_token.return_value = (
            "test_external_user_id"
        )
        mock_get_existing_user_and_update_admin_status.return_value = None
        response = Mock()
        response.status_code = 200
        mock_request_get.return_value = response
        user_data = Mock()
        response.json.return_value = {"data": user_data}
        user = Mock()
        mock_check_for_inactive_user_with_same_email_address.return_value = user

        result = CoopsPtAuthBackend().authenticate(request, **kwargs)

        self.assertEqual(user, result)
        mock_do_remote_login.assert_called_once_with(request, **kwargs)
        mock_get_external_user_id_from_access_token.assert_called_once_with(
            "test_access_token"
        )
        mock_get_existing_user_and_update_admin_status.assert_called_once_with(
            external_user_id="test_external_user_id", access_token="test_access_token"
        )
        mock_request_get.assert_called_once_with(
            "users/test_external_user_id", **kwargs
        )
        mock_check_for_inactive_user_with_same_email_address.assert_called_once_with(
            user_data=user_data
        )

    @patch("tapir.rizoma.coops_pt_auth_backend.transaction", autospec=True)
    @patch.object(
        CoopsPtAuthBackend, "create_tapir_user_and_link_with_share_owner", autospec=True
    )
    @patch.object(
        CoopsPtAuthBackend,
        "check_for_inactive_user_with_same_email_address",
        autospec=True,
    )
    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    @patch.object(
        CoopsPtAuthBackend, "get_existing_user_and_update_admin_status", autospec=True
    )
    @patch.object(
        CoopsPtLoginManager, "get_external_user_id_from_access_token", autospec=True
    )
    @patch.object(CoopsPtAuthBackend, "do_remote_login", autospec=True)
    def test_authenticate_userDoesntExist_createsAndReturnsUser(
        self,
        mock_do_remote_login: Mock,
        mock_get_external_user_id_from_access_token: Mock,
        mock_get_existing_user_and_update_admin_status: Mock,
        mock_request_get: Mock,
        mock_check_for_inactive_user_with_same_email_address: Mock,
        mock_create_tapir_user_and_link_with_share_owner: Mock,
        mock_transaction: Mock,
    ):
        request = Mock()
        kwargs = {}
        mock_do_remote_login.return_value = "test_access_token"
        mock_get_external_user_id_from_access_token.return_value = (
            "test_external_user_id"
        )
        mock_get_existing_user_and_update_admin_status.return_value = None
        response = Mock()
        response.status_code = 200
        mock_request_get.return_value = response
        user_data = Mock()
        response.json.return_value = {"data": user_data}
        mock_check_for_inactive_user_with_same_email_address.return_value = None
        user = Mock()
        mock_create_tapir_user_and_link_with_share_owner.return_value = user
        atomic = Mock()
        atomic.__enter__ = Mock()
        atomic.__exit__ = Mock()
        mock_transaction.atomic.return_value = atomic

        result = CoopsPtAuthBackend().authenticate(request, **kwargs)

        self.assertEqual(user, result)
        mock_do_remote_login.assert_called_once_with(request, **kwargs)
        mock_get_external_user_id_from_access_token.assert_called_once_with(
            "test_access_token"
        )
        mock_get_existing_user_and_update_admin_status.assert_called_once_with(
            external_user_id="test_external_user_id", access_token="test_access_token"
        )
        mock_request_get.assert_called_once_with(
            "users/test_external_user_id", **kwargs
        )
        mock_check_for_inactive_user_with_same_email_address.assert_called_once_with(
            user_data=user_data
        )
        mock_create_tapir_user_and_link_with_share_owner.assert_called_once_with(
            user_data
        )

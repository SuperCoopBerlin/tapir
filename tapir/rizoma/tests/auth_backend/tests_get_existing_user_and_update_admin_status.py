from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.services.coops_pt_login_manager import CoopsPtLoginManager


class TestsGetExistingUserAndUpdateAdminStatus(SimpleTestCase):
    @patch.object(CoopsPtLoginManager, "get_role_from_access_token", autospec=True)
    @patch.object(TapirUser, "objects")
    def test_getExistingUserAndUpdateAdminStatus_userDoesntExist_returnsNone(
        self, mock_tapir_user_objects: Mock, mock_get_role_from_access_token: Mock
    ):
        mock_tapir_user_objects.filter.return_value.first.return_value = None

        result = CoopsPtAuthBackend.get_existing_user_and_update_admin_status(
            external_user_id="test_id", access_token="test_token"
        )

        self.assertIsNone(result)
        mock_get_role_from_access_token.assert_not_called()

    @patch.object(CoopsPtLoginManager, "get_role_from_access_token", autospec=True)
    @patch.object(TapirUser, "objects")
    def test_getExistingUserAndUpdateAdminStatus_userExistsAndAdminStatusIsAlreadyCorrect_doesNothingAndReturnsUser(
        self, mock_tapir_user_objects: Mock, mock_get_role_from_access_token: Mock
    ):
        user = TapirUserFactory.build(is_superuser=False)
        mock_tapir_user_objects.filter.return_value.first.return_value = user
        mock_get_role_from_access_token.return_value = ""

        result = CoopsPtAuthBackend.get_existing_user_and_update_admin_status(
            external_user_id="test_id", access_token="test_token"
        )

        self.assertEqual(user, result)
        mock_get_role_from_access_token.assert_called_once_with("test_token")

    @patch.object(CoopsPtLoginManager, "get_role_from_access_token", autospec=True)
    @patch.object(TapirUser, "objects")
    def test_getExistingUserAndUpdateAdminStatus_userExistsAndAdminStatusMustBeUpdate_savesAndReturnsUser(
        self, mock_tapir_user_objects: Mock, mock_get_role_from_access_token: Mock
    ):
        user = Mock()
        user.is_superuser = False
        mock_tapir_user_objects.filter.return_value.first.return_value = user
        mock_get_role_from_access_token.return_value = "admin"

        result = CoopsPtAuthBackend.get_existing_user_and_update_admin_status(
            external_user_id="test_id", access_token="test_token"
        )

        self.assertEqual(user, result)
        mock_get_role_from_access_token.assert_called_once_with("test_token")
        self.assertTrue(user.is_superuser)
        user.save.assert_called_once_with()

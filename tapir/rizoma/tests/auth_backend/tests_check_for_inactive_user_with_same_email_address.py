from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.accounts.models import TapirUser
from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator


class TestsCheckForInactiveUserWithSameEmailAddress(SimpleTestCase):
    @patch.object(TapirUser, "objects")
    def test_checkForInactiveUserWithSameEmailAddress_userDoesntExist_returnsNone(
        self, mock_tapir_user_objects: Mock
    ):
        user_data = {"email": "test_email"}
        mock_tapir_user_objects.filter.return_value.first.return_value = None

        result = CoopsPtAuthBackend.check_for_inactive_user_with_same_email_address(
            user_data
        )

        self.assertIsNone(result)
        mock_tapir_user_objects.filter.assert_called_once_with(
            username="test_email", is_active=False
        )
        mock_tapir_user_objects.filter.return_value.first.assert_called_once_with()

    @patch.object(CoopsPtUserCreator, "set_attributes_from_api_response", autospec=True)
    @patch.object(TapirUser, "objects")
    def test_checkForInactiveUserWithSameEmailAddress_userExists_updatesAndReturnsUser(
        self, mock_tapir_user_objects: Mock, mock_set_attributes_from_api_response: Mock
    ):
        user_data = {
            "email": "test_email",
        }
        user = Mock()
        mock_tapir_user_objects.filter.return_value.first.return_value = user

        result = CoopsPtAuthBackend.check_for_inactive_user_with_same_email_address(
            user_data
        )

        self.assertEqual(user, result)
        self.assertTrue(user.is_active)
        user.save.assert_called_once_with()
        mock_tapir_user_objects.filter.assert_called_once_with(
            username="test_email", is_active=False
        )
        mock_tapir_user_objects.filter.return_value.first.assert_called_once_with()
        mock_set_attributes_from_api_response.assert_called_once_with(
            tapir_user=user, user_json=user_data
        )

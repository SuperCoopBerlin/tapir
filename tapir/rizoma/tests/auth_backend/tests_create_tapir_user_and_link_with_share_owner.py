from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator


class TestsCreateTapirUserAndLinkWithShareOwner(SimpleTestCase):
    @patch.object(CoopsPtUserCreator, "fetch_and_create_share_owner", autospec=True)
    @patch.object(
        CoopsPtUserCreator, "build_tapir_user_from_api_response", autospec=True
    )
    def test_createTapirUserAndLinkWithShareOwner_noMemberIdInUserData_createsTapirUserButNotShareOwner(
        self,
        mock_build_tapir_user_from_api_response: Mock,
        mock_fetch_and_create_share_owner: Mock,
    ):
        user_data = {"memberId": None}
        user = Mock()
        mock_build_tapir_user_from_api_response.return_value = user

        result = CoopsPtAuthBackend.create_tapir_user_and_link_with_share_owner(
            user_data
        )

        mock_fetch_and_create_share_owner.assert_not_called()
        self.assertEqual(user, result)
        user.save.assert_called_once_with()

    @patch.object(CoopsPtUserCreator, "fetch_and_create_share_owner", autospec=True)
    @patch.object(
        CoopsPtUserCreator, "build_tapir_user_from_api_response", autospec=True
    )
    def test_createTapirUserAndLinkWithShareOwner_memberIdPresentInUserData_createsTapirUserAndShareOwner(
        self,
        mock_build_tapir_user_from_api_response: Mock,
        mock_fetch_and_create_share_owner: Mock,
    ):
        user_data = {"memberId": "test_member_id"}
        user = Mock()
        mock_build_tapir_user_from_api_response.return_value = user

        result = CoopsPtAuthBackend.create_tapir_user_and_link_with_share_owner(
            user_data
        )

        mock_fetch_and_create_share_owner.assert_called_once_with(
            "test_member_id", user
        )
        self.assertEqual(user, result)
        user.save.assert_called_once_with()

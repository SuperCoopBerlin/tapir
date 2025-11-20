from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.rizoma.exceptions import CoopsPtRequestException
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler
from tapir.rizoma.services.group_affiliation_checker import GroupAffiliationChecker


class TestGroupAffiliationChecker(SimpleTestCase):
    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    def test_isMemberAffiliationToGroupActive_responseCodeIsNot200_raisesError(
        self, mock_get: Mock
    ):
        response = Mock()
        response.status_code = 400
        mock_get.return_value = response

        with self.assertRaises(CoopsPtRequestException):
            GroupAffiliationChecker.is_member_affiliation_to_group_active(
                external_id="test_id", group_name="test_group"
            )

        mock_get.assert_called_once_with("members/test_id/member_states")

    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    def test_isMemberAffiliationToGroupActive_memberIsNotInAnyGroup_returnsFalse(
        self, mock_get: Mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": []}
        mock_get.return_value = response

        result = GroupAffiliationChecker.is_member_affiliation_to_group_active(
            external_id="test_id", group_name="test_group"
        )

        self.assertFalse(result)
        mock_get.assert_called_once_with("members/test_id/member_states")

    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    def test_isMemberAffiliationToGroupActive_memberIsOnlyInOtherGroups_returnsFalse(
        self, mock_get: Mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [{"_memberStateName": "other_group", "status": "Activo"}]
        }
        mock_get.return_value = response

        result = GroupAffiliationChecker.is_member_affiliation_to_group_active(
            external_id="test_id", group_name="target_group"
        )

        self.assertFalse(result)
        mock_get.assert_called_once_with("members/test_id/member_states")

    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    def test_isMemberAffiliationToGroupActive_memberIsInTargetGroupButInactive_returnsFalse(
        self, mock_get: Mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {"_memberStateName": "other_group", "status": "Activo"},
                {
                    "_memberStateName": "target_group",
                    "status": "some not active status",
                },
            ]
        }
        mock_get.return_value = response

        result = GroupAffiliationChecker.is_member_affiliation_to_group_active(
            external_id="test_id", group_name="target_group"
        )

        self.assertFalse(result)
        mock_get.assert_called_once_with("members/test_id/member_states")

    @patch.object(CoopsPtRequestHandler, "get", autospec=True)
    def test_isMemberAffiliationToGroupActive_memberIsInTargetGroupAndActive_returnsTrue(
        self, mock_get: Mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {"_memberStateName": "other_group", "status": "Activo"},
                {
                    "_memberStateName": "target_group",
                    "status": "Activo",
                },
            ]
        }
        mock_get.return_value = response

        result = GroupAffiliationChecker.is_member_affiliation_to_group_active(
            external_id="test_id", group_name="target_group"
        )

        self.assertTrue(result)
        mock_get.assert_called_once_with("members/test_id/member_states")

from http import HTTPStatus

from django.urls import reverse

from tapir import settings
from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    PermissionTestMixin,
)


class TestMembershipResignationListView(
    PermissionTestMixin, FeatureFlagTestMixin, TapirFactoryTestBase
):

    def permission_test_get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
            settings.GROUP_MEMBER_OFFICE,
            settings.GROUP_ACCOUNTING,
        ]

    def permission_test_do_request(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        return self.client.get(reverse("coop:membership_resignation_list"))

    def test_membershipResignationListView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_member_office_user()
        response = self.client.get(reverse("coop:membership_resignation_list"))
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

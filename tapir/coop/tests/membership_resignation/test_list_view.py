from http import HTTPStatus

from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import FeatureFlagTestMixin, TapirFactoryTestBase


class TestMembershipResignationListView(FeatureFlagTestMixin, TapirFactoryTestBase):

    def test_membershipResignationListView_loggedInAsNormalUser_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        self.login_as_normal_user()
        response = self.client.get(reverse("coop:resigned_members_list"))
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    def test_membershipResignationListView_loggedInAsMemberOffice_accessGranted(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        self.login_as_member_office_user()
        response = self.client.get(reverse("coop:resigned_members_list"))
        self.assertStatusCode(response, HTTPStatus.OK)

    def test_membershipResignationListView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_member_office_user()
        response = self.client.get(reverse("coop:resigned_members_list"))
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

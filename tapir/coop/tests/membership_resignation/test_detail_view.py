from http import HTTPStatus

from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import MembershipResignation
from tapir.coop.tests.factories import MembershipResignationFactory
from tapir.utils.tests_utils import FeatureFlagTestMixin, TapirFactoryTestBase


class TestMembershipResignationDetailView(FeatureFlagTestMixin, TapirFactoryTestBase):

    def test_membershipResignationDetailView_loggedInAsNormalUser_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        self.login_as_normal_user()
        resignation: MembershipResignation = MembershipResignationFactory.create()

        response = self.client.get(
            reverse("coop:resignedmember_detail", args=[resignation.id])
        )

        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    def test_membershipResignationDetailView_loggedInAsMemberOffice_accessGranted(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        self.login_as_member_office_user()
        resignation: MembershipResignation = MembershipResignationFactory.create()

        response = self.client.get(
            reverse("coop:resignedmember_detail", args=[resignation.id])
        )

        self.assertStatusCode(response, HTTPStatus.OK)

    def test_membershipResignationDetailView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_member_office_user()
        resignation: MembershipResignation = MembershipResignationFactory.create()

        response = self.client.get(
            reverse("coop:resignedmember_detail", args=[resignation.id])
        )

        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

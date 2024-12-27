from http import HTTPStatus

from django.urls import reverse

from tapir import settings
from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import MembershipResignation
from tapir.coop.tests.factories import MembershipResignationFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    PermissionTestMixin,
)


class TestMembershipResignationDetailView(
    PermissionTestMixin, FeatureFlagTestMixin, TapirFactoryTestBase
):

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
            settings.GROUP_MEMBER_OFFICE,
            settings.GROUP_ACCOUNTING,
        ]

    def do_request(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        resignation: MembershipResignation = MembershipResignationFactory.create()
        return self.client.get(
            reverse("coop:membership_resignation_detail", args=[resignation.id])
        )

    def test_membershipResignationDetailView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_member_office_user()
        resignation: MembershipResignation = MembershipResignationFactory.create()

        response = self.client.get(
            reverse("coop:membership_resignation_detail", args=[resignation.id])
        )

        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

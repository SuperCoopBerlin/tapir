from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import MembershipResignation
from tapir.coop.tests.factories import MembershipResignationFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
)


class TestMembershipResignationQuerySet(FeatureFlagTestMixin, TapirFactoryTestBase):
    def setUp(self):
        super().setUp()
        self.login_as_vorstand()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        self.resignation1 = MembershipResignationFactory.create()
        self.resignation2 = MembershipResignationFactory.create()

    def test_membershipresignationQuerySet_withExplicitID_queryShouldFindIDAndExcludeOthers(
        self,
    ):
        search_results = MembershipResignation.objects.with_name_or_id(
            str(self.resignation1.share_owner.id)
        )
        self.assertQuerySetEqual(
            search_results,
            [self.resignation1],
        )

    def test_membershipresignationqueryset_withExplicitName_queryShouldFindFirstOrLastNameAndExcludeOthers(
        self,
    ):
        search_string1 = f"{self.resignation1.share_owner.first_name} {self.resignation1.share_owner.last_name}"
        search_result = MembershipResignation.objects.with_name_or_id(search_string1)
        self.assertQuerySetEqual(
            search_result,
            [self.resignation1],
        )
        self.assertNotIn(self.resignation2, search_result)

    def test_membershipresignationqueryset_withInvalidIDAndName_queryShouldBeEmpty(
        self,
    ):
        search_string = "foo"
        search_result = MembershipResignation.objects.with_name_or_id(search_string)
        self.assertQuerySetEqual(search_result, [])

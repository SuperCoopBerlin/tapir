from django.urls import reverse

from tapir.statistics import config
from tapir.utils.tests_utils import TapirFactoryTestBase, FeatureFlagTestMixin


class TestMainStatisticsViewAccess(FeatureFlagTestMixin, TapirFactoryTestBase):
    VIEW_NAME = "statistics:main_statistics"

    def test_featureFlagOff_normalMemberDoesNotHaveAccess(self):
        self.given_feature_flag_value(
            config.FEATURE_FLAG_NAME_UPDATED_STATS_PAGE_09_23, False
        )
        self.login_as_normal_user()
        response = self.client.get(reverse(self.VIEW_NAME))
        self.assertEqual(403, response.status_code)

    def test_featureFlagOn_normalMemberHasAccess(self):
        self.given_feature_flag_value(
            config.FEATURE_FLAG_NAME_UPDATED_STATS_PAGE_09_23, True
        )
        self.login_as_normal_user()
        response = self.client.get(reverse(self.VIEW_NAME))
        self.assertEqual(200, response.status_code)

    def test_always_VorstandHasAccess(self):
        self.login_as_vorstand()
        response = self.client.get(reverse(self.VIEW_NAME))
        self.assertEqual(200, response.status_code)

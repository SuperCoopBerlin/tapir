import datetime

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestMembershipResignationService(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_todo(self):
        self.fail("TODO, test service functions.")

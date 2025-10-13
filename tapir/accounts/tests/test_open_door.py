from django.urls import reverse

from tapir.accounts.config import feature_flag_open_door
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, FeatureFlagTestMixin


class TestOpenDoorFeature(FeatureFlagTestMixin, TapirFactoryTestBase):
    """Test the door opening feature with feature flag support."""

    def test_open_door_action_with_feature_enabled(self):
        """Test that door opening works when feature flag is enabled."""
        self.given_feature_flag_value(feature_flag_open_door, True)
        
        user = TapirUserFactory.create()
        self.login_as_user(user)
        
        response = self.client.post(
            reverse("accounts:open_door")
        )
        self.assertEqual(200, response.status_code)

    def test_open_door_action_with_feature_disabled(self):
        """Test that door opening is blocked when feature flag is disabled."""
        self.given_feature_flag_value(feature_flag_open_door, False)
        
        user = TapirUserFactory.create()
        self.login_as_user(user)
        
        response = self.client.post(
            reverse("accounts:open_door")
        )
        self.assertEqual(403, response.status_code)

    def test_get_open_door_status_with_feature_enabled(self):
        """Test that status endpoint works when feature flag is enabled."""
        self.given_feature_flag_value(feature_flag_open_door, True)
        
        # Status should be 403 when no door opening was triggered
        response = self.client.get(reverse("accounts:open_door"))
        self.assertEqual(403, response.status_code)

    def test_get_open_door_status_with_feature_disabled(self):
        """Test that status endpoint returns 403 when feature flag is disabled."""
        self.given_feature_flag_value(feature_flag_open_door, False)
        
        response = self.client.get(reverse("accounts:open_door"))
        self.assertEqual(403, response.status_code)

    def test_open_door_requires_authentication(self):
        """Test that door opening requires authentication."""
        self.given_feature_flag_value(feature_flag_open_door, True)
        
        user = TapirUserFactory.create()
        
        # Try without login
        response = self.client.post(
            reverse("accounts:open_door")
        )
        # Should redirect to login page
        self.assertEqual(302, response.status_code)


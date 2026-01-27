import datetime

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.config import cache_key_open_door
from tapir.accounts.config import feature_flag_open_door
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwnership
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.shifts.models import ShiftUserData
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    FeatureFlagTestMixin,
    create_member_that_can_shop,
)


class TestOpenDoorFeature(FeatureFlagTestMixin, TapirFactoryTestBase):
    """Test the door opening feature with feature flag support."""

    def test_openDoor_postWithFeatureEnabledAndUserWithoutShareOwner_returnsForbidden(
        self,
    ):
        """Test that door opening is blocked when user has no share_owner."""
        self.given_feature_flag_value(feature_flag_open_door, True)

        # Create user and delete their share_owner
        user = TapirUserFactory.create()
        user.share_owner.delete()
        self.login_as_user(user)

        response = self.client.post(reverse("accounts:open_door"))
        self.assertStatusCode(response, 403)

    def test_openDoor_postWithFeatureDisabledAndAuthenticated_returnsForbidden(self):
        """Test that door opening is blocked when feature flag is disabled."""
        self.given_feature_flag_value(feature_flag_open_door, False)

        user = TapirUserFactory.create()
        self.login_as_user(user)

        response = self.client.post(reverse("accounts:open_door"))
        self.assertStatusCode(response, 403)

    def test_openDoor_getWithFeatureEnabledAndNotTriggered_returnsForbidden(self):
        """Test that status endpoint works when feature flag is enabled."""
        self.given_feature_flag_value(feature_flag_open_door, True)

        # Status should be 403 when no door opening was triggered
        response = self.client.get(reverse("accounts:open_door"))
        self.assertStatusCode(response, 403)

    def test_openDoor_getWithFeatureEnabledAndTriggered_returnsOk(self):
        """Test that status endpoint works when feature flag is enabled."""
        self.given_feature_flag_value(feature_flag_open_door, True)

        user = TapirUserFactory.create()
        self.login_as_user(user)

        cache.set(cache_key_open_door, True)

        response = self.client.get(reverse("accounts:open_door"))
        self.assertStatusCode(response, 200)

    def test_openDoor_getWithFeatureDisabled_returnsForbidden(self):
        """Test that status endpoint returns 403 when feature flag is disabled."""
        self.given_feature_flag_value(feature_flag_open_door, False)

        response = self.client.get(reverse("accounts:open_door"))
        self.assertStatusCode(response, 403)

    def test_openDoor_postRequiresAuthentication_returnsRedirect(self):
        """Test that door opening requires authentication."""
        self.given_feature_flag_value(feature_flag_open_door, True)

        user = TapirUserFactory.create()

        # Try without login
        response = self.client.post(reverse("accounts:open_door"))
        # Should redirect to login page
        self.assertStatusCode(response, 302)

    def test_openDoor_postWithMemberCanShop_returnsOk(self):
        """Test that door opening works when member can shop."""
        self.given_feature_flag_value(feature_flag_open_door, True)

        reference_time = timezone.now()
        user = create_member_that_can_shop(self, reference_time)
        self.login_as_user(user)

        response = self.client.post(reverse("accounts:open_door"))
        self.assertStatusCode(response, 200)

    def test_openDoor_postWithFrozenMember_returnsOk(self):
        """Test that door opening works even when member is frozen."""
        self.given_feature_flag_value(feature_flag_open_door, True)

        # Create a frozen member who cannot shop
        user = TapirUserFactory.create(
            share_owner__nb_shares=1,
            share_owner__is_investing=False,
            date_joined=timezone.now() - datetime.timedelta(days=1),
        )
        ShareOwnership.objects.update(
            start_date=(timezone.now() - datetime.timedelta(days=1)).date()
        )
        ShiftUserData.objects.update(is_frozen=True)

        self.login_as_user(user)

        # Verify that member cannot shop (but can still open door)
        self.assertFalse(
            MemberCanShopService.can_shop(user.share_owner, timezone.now())
        )

        response = self.client.post(reverse("accounts:open_door"))
        self.assertStatusCode(response, 200)

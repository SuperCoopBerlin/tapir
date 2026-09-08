from urllib.parse import urlencode

from django.urls import reverse

from tapir.coop.config import (
    feature_flag_buy_shares,
)
from tapir.core.models import FeatureFlag
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestRequestShareGenericView(TapirFactoryTestBase):
    @classmethod
    def setUpTestData(cls):
        FeatureFlag.ensure_flag_exists(feature_flag_buy_shares)
        FeatureFlag.set_flag_value(feature_flag_buy_shares, True)

    def setUp(self):
        self.url = reverse("coop:share_create_generic")

    def test_get_userHasNoShareOwner_redirectsToUserProfile(self):
        user = self.login_as_normal_user(share_owner=None)

        response = self.client.get(self.url)

        self.assertRedirects(
            response=response,
            expected_url=reverse("accounts:user_detail", args=[user.id]),
        )

    def test_get_userHasShareOwner_redirectsToShareRequestPage(self):
        user = self.login_as_normal_user()

        response = self.client.get(self.url)

        self.assertRedirects(
            response=response,
            expected_url=reverse("coop:share_create", args=[user.share_owner.id]),
        )

    def test_get_notLoggedIn_redirectsToLoginPage(self):
        response = self.client.get(self.url)

        base_url = reverse("login")
        final_url = f"{base_url}?{urlencode({"next":self.url})}"

        self.assertRedirects(response=response, expected_url=final_url)

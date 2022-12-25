from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestPurchaseTrackingSetting(TapirFactoryTestBase):
    def test_normal_user_can_update_their_own_setting(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=False)
        self.login_as_user(tapir_user)

        response = self.client.get(
            reverse(
                "accounts:update_purchase_tracking_allowed", args=[tapir_user.pk, 1]
            ),
        )

        self.assertRedirects(
            response=response, expected_url=tapir_user.get_absolute_url()
        )
        tapir_user.refresh_from_db()
        self.assertEqual(True, tapir_user.allows_purchase_tracking)

    def test_other_user_cant_update_tracking_setting(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=False)
        self.login_as_member_office_user()

        response = self.client.get(
            reverse(
                "accounts:update_purchase_tracking_allowed", args=[tapir_user.pk, 1]
            ),
        )

        self.assertEqual(403, response.status_code)
        tapir_user.refresh_from_db()
        self.assertEqual(False, tapir_user.allows_purchase_tracking)

from django.urls import reverse
from tapir import settings

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import (
    PermissionTestMixin,
    TapirFactoryTestBase,
    FeatureFlagTestMixin,
)


class TestFinancialMattersVisibility(
    PermissionTestMixin, FeatureFlagTestMixin, TapirFactoryTestBase
):

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
        ]

    def do_request(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        return self.client.get(
            reverse("accounts:member_card_barcode_pdf", args=[tapir_user.id])
        )

    def test_financialMattersOnUserDetailPage_loggedInAsRespectiveUser_isAllowedToSee(
        self,
    ):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        self.login_as_user(tapir_user)
        response = self.client.get(
            reverse("accounts:user_detail", args=[tapir_user.id])
        )
        self.assertContains(response, "purchases-tracking-card")
        self.assertContains(response, "purchases-card")
        self.assertContains(response, "card-account-card")

    def test_financialMattersOnUserDetailPage_loggedInAsVorstand_isAllowedToSee(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        self.login_as_vorstand()
        response = self.client.get(
            reverse("accounts:user_detail", args=[tapir_user.id])
        )
        self.assertContains(response, "purchases-tracking-card")
        self.assertContains(response, "purchases-card")
        self.assertContains(response, "card-account-card")

    def test_financialMattersOnUserDetailPage_loggedInAsMemberOffice_isNotAllowedToSee(
        self,
    ):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        self.login_as_member_office_user()
        response = self.client.get(
            reverse("accounts:user_detail", args=[tapir_user.id])
        )
        self.assertContains(
            response, "purchases-tracking-card"
        )  # header should be shown
        self.assertNotContains(response, "card-account-card")
        self.assertNotContains(response, "purchases-card")

        self.assertContains(
            response,
            "You can only look at your own barcode unless you have admin right",
        )

    def test_financialMattersOnUserDetailPage_loggedInAsVorstand_hideCardsAfterDisablingPurchaseTracking(
        self,
    ):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        tapir_user.allows_purchase_tracking = False
        tapir_user.save()
        self.login_as_vorstand()
        response = self.client.get(
            reverse("accounts:user_detail", args=[tapir_user.id])
        )
        self.assertContains(
            response, "purchases-tracking-card"
        )  # header should be shown
        self.assertNotContains(response, "card-account-card")
        self.assertNotContains(response, "purchases-card")

from django.urls import reverse

from tapir import settings
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import (
    PermissionTestMixin,
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
)


class TestShareOwnerDeleteView(
    PermissionTestMixin, FeatureFlagTestMixin, TapirFactoryTestBase
):
    def setUp(self) -> None:
        super().setUp()

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
        ]

    def do_request(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        return self.client.post(
            reverse("coop:shareowner_delete", args=[tapir_user.share_owner.id]),
            follow=True,
        )

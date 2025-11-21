from http import HTTPStatus

from django.urls import reverse

from tapir import settings
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import DeleteShareOwnerLogEntry, ShareOwner
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
        tapir_user = TapirUserFactory()
        return self.client.post(
            reverse("coop:shareowner_delete", args=[tapir_user.share_owner.id]),
            follow=True,
        )

    def test_ShareOwnerDeleteView_shareOwnerdeletedAt_hasDate(self):
        self.login_as_vorstand()
        tapir_user = TapirUserFactory()
        response = self.client.post(
            reverse("coop:shareowner_delete", args=[tapir_user.share_owner.id]),
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)
        tapir_user.share_owner.refresh_from_db()
        self.assertIsNotNone(tapir_user.share_owner.deleted_at)
        self.assertEqual(DeleteShareOwnerLogEntry.objects.count(), 1)

    def test_ShareOwnerDeleteView_normalShareOwner_cannotDeleteItself(self):
        tapir_user = self.login_as_normal_user()
        response = self.client.post(
            reverse("coop:shareowner_delete", args=[tapir_user.share_owner.id]),
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)
        tapir_user.share_owner.refresh_from_db()
        self.assertIsNone(tapir_user.share_owner.deleted_at)
        self.assertEqual(DeleteShareOwnerLogEntry.objects.count(), 0)

    def test_ShareOwnerDeleteView_vorstandShareOwner_cannotDeleteItself(self):
        tapir_user = self.login_as_vorstand()
        response = self.client.post(
            reverse("coop:shareowner_delete", args=[tapir_user.share_owner.id]),
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)
        tapir_user.share_owner.refresh_from_db()
        self.assertIsNone(tapir_user.share_owner.deleted_at)
        self.assertEqual(DeleteShareOwnerLogEntry.objects.count(), 0)

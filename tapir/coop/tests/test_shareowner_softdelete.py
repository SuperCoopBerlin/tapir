import pytest
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShareOwnershipSoftDelete(TapirFactoryTestBase):
    def test_softDelete_DeletedAt_isNotNone(self):
        share_owner = ShareOwnerFactory.create()

        self.assertIsNone(share_owner.deleted_at)
        share_owner.soft_delete()

        share_owner.refresh_from_db()

        self.assertIsNotNone(share_owner.deleted_at)
        self.assertLessEqual(share_owner.deleted_at, timezone.now())

    def test_softDelete_restoreDeleted_isNone(self):
        share_owner = ShareOwnerFactory.create()

        share_owner.soft_delete()
        share_owner.refresh_from_db()
        self.assertIsNotNone(share_owner.deleted_at)

        share_owner.restore()
        share_owner.refresh_from_db()

        self.assertIsNone(share_owner.deleted_at)

    def test_softDelete_nonDeletedManager_containsNotDeletedShareowners(self):
        active_owner = ShareOwnerFactory.create()

        soft_deleted_owner = ShareOwnerFactory.create()
        soft_deleted_owner.soft_delete()

        non_deleted_owners = ShareOwner.objects.all()
        self.assertIn(active_owner, non_deleted_owners)
        self.assertNotIn(soft_deleted_owner, non_deleted_owners)

    def test_softDelete_everythingManager_containsAlsoDeletedShareowners(self):
        owner1 = ShareOwnerFactory.create()

        owner2 = ShareOwnerFactory.create()
        owner2.soft_delete()

        all_owners = ShareOwner.everything.all()

        self.assertIn(owner1, all_owners)
        self.assertIn(owner2, all_owners)

    def test_hardDelete_shareOwner_isfullyDeleted(self):
        share_owner = ShareOwnerFactory.create()
        all_users = ShareOwner.everything.all()
        self.assertIn(share_owner, all_users)
        share_owner.delete()

        all_users = ShareOwner.everything.all()
        self.assertNotIn(share_owner, all_users)

    def test_delete_cannotDeleteOwnAccount(self):
        vorstand_user = self.login_as_vorstand()
        response = self.client.post(
            reverse("coop:shareowner_delete", args=[vorstand_user.share_owner.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn(vorstand_user.share_owner, ShareOwner.everything.all())

import pytest
from django.utils import timezone

from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShareOwnershipSoftDelete(TapirFactoryTestBase):
    def test_softDelete_DeletedAt_isNotNone(self):
        share_owner = ShareOwnerFactory.create()

        assert share_owner.deleted_at is None

        share_owner.soft_delete()

        share_owner.refresh_from_db()

        assert share_owner.deleted_at is not None
        assert share_owner.deleted_at <= timezone.now()

    def test_softDelete_restoreDeleted_isNone(self):
        share_owner = ShareOwnerFactory.create()

        share_owner.soft_delete()
        share_owner.refresh_from_db()
        assert share_owner.deleted_at is not None

        share_owner.restore()
        share_owner.refresh_from_db()

        assert share_owner.deleted_at is None

    def test_softDelete_nonDeletedManager_containsNotDeletedShareowners(self):
        active_owner = ShareOwnerFactory.create()

        soft_deleted_owner = ShareOwnerFactory.create()
        soft_deleted_owner.soft_delete()

        non_deleted_owners = ShareOwner.objects.all()

        assert active_owner in non_deleted_owners
        assert soft_deleted_owner not in non_deleted_owners

    def test_softDelete_everythingManager_containsAlsoDeletedShareowners(self):
        owner1 = ShareOwnerFactory.create()

        owner2 = ShareOwnerFactory.create()
        owner2.soft_delete()

        all_owners = ShareOwner.everything.all()

        assert owner1 in all_owners
        assert owner2 in all_owners

    def test_hardDelete_shareOwner_isfullyDeleted(self):
        share_owner = ShareOwnerFactory.create()
        all_users = ShareOwner.everything.all()
        assert share_owner in all_users

        share_owner.delete()

        all_users = ShareOwner.everything.all()
        assert share_owner not in all_users

from django.test import SimpleTestCase

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend


class TestsUpdateAdminStatus(SimpleTestCase):
    def test_updateAdminStatus_userShouldBeAdminAndIsAdmin_doesNothingAndReturnsFalse(
        self,
    ):
        user = TapirUserFactory.build(is_superuser=True)

        result = CoopsPtAuthBackend.update_admin_status(user=user, role="admin")

        self.assertEqual(user.is_superuser, True)
        self.assertFalse(result)

    def test_updateAdminStatus_userShouldBeAdminAndIsNotAdmin_setsSuperuserAndReturnsTrue(
        self,
    ):
        user = TapirUserFactory.build(is_superuser=False)

        result = CoopsPtAuthBackend.update_admin_status(user=user, role="admin")

        self.assertEqual(user.is_superuser, True)
        self.assertTrue(result)

    def test_updateAdminStatus_userShouldNotBeAdminAndIsNotAdmin_doesNothingAndReturnsFalse(
        self,
    ):
        user = TapirUserFactory.build(is_superuser=False)

        result = CoopsPtAuthBackend.update_admin_status(user=user, role="")

        self.assertEqual(user.is_superuser, False)
        self.assertFalse(result)

    def test_updateAdminStatus_userShouldNotBeAdminAndIsAdmin_setsSuperuserAndReturnsTrue(
        self,
    ):
        user = TapirUserFactory.build(is_superuser=True)

        result = CoopsPtAuthBackend.update_admin_status(user=user, role="")

        self.assertEqual(user.is_superuser, False)
        self.assertTrue(result)

import pytest
from django.conf import settings
from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.settings import LOGIN_BACKEND_LDAP
from tapir.utils.tests_utils import TapirFactoryTestBase


@pytest.mark.skipif(
    settings.ACTIVE_LOGIN_BACKEND != LOGIN_BACKEND_LDAP,
    reason="These tests are exclusive to the ldap login backend",
)
class TestUsernameChange(TapirFactoryTestBase):
    OLD_USERNAME = "old.username"
    NEW_USERNAME = "new.username"

    def test_normal_user_can_update_own_username(self):
        actor: TapirUser = TapirUserFactory.create(
            is_in_member_office=False, username=self.OLD_USERNAME
        )
        self.assertTrue(
            self.client.login(username=self.OLD_USERNAME, password=self.OLD_USERNAME)
        )

        response = self.try_update(actor=actor, target=actor)
        self.assertEqual(200, response.status_code)

        actor.refresh_from_db()

        self.assertEqual(self.NEW_USERNAME, actor.username)
        self.assertTrue(
            self.client.login(username=self.NEW_USERNAME, password=self.OLD_USERNAME)
        )

    def test_normal_user_cannot_update_other_username(self):
        actor: TapirUser = TapirUserFactory.create(is_in_member_office=False)
        target: TapirUser = TapirUserFactory.create(username=self.OLD_USERNAME)

        response = self.try_update(actor=actor, target=target)
        self.assertEqual(403, response.status_code)

        target.refresh_from_db()
        self.assertEqual(self.OLD_USERNAME, target.username)
        self.assertTrue(
            self.client.login(username=self.OLD_USERNAME, password=self.OLD_USERNAME)
        )

    def test_member_office_user_can_update_other_username(self):
        actor: TapirUser = TapirUserFactory.create(is_in_member_office=True)
        target: TapirUser = TapirUserFactory.create(username=self.OLD_USERNAME)
        self.assertTrue(
            self.client.login(username=self.OLD_USERNAME, password=self.OLD_USERNAME)
        )

        response = self.try_update(actor=actor, target=target)
        self.assertEqual(200, response.status_code)

        target.refresh_from_db()
        self.assertEqual(self.NEW_USERNAME, target.username)
        self.assertTrue(
            self.client.login(username=self.NEW_USERNAME, password=self.OLD_USERNAME)
        )

    def try_update(self, actor: TapirUser, target: TapirUser):
        self.login_as_user(actor)

        return self.client.post(
            reverse("accounts:edit_username", args=[target.id]),
            {"username": self.NEW_USERNAME},
            follow=True,
        )

    def test_cannot_create_duplicate_username_case_sensitive(self):
        target = TapirUserFactory.create(username="lisa")
        TapirUserFactory.create(username="bart")
        self.login_as_member_office_user()

        response = self.client.post(
            reverse("accounts:edit_username", args=[target.id]),
            {"username": "bart"},
        )
        self.assertEqual(200, response.status_code)

        self.assertIn("username", response.context["form"].errors.keys())
        target.refresh_from_db()
        self.assertEqual("lisa", target.username)
        self.assertTrue(self.client.login(username="lisa", password="lisa"))

    def test_cannot_create_duplicate_username_case_insensitive(self):
        target = TapirUserFactory.create(username="lisa")
        TapirUserFactory.create(username="bart")
        self.login_as_member_office_user()

        response = self.client.post(
            reverse("accounts:edit_username", args=[target.id]),
            {"username": "Bart"},
        )
        self.assertEqual(200, response.status_code)

        self.assertIn("username", response.context["form"].errors.keys())
        target.refresh_from_db()
        self.assertEqual("lisa", target.username)
        self.assertTrue(self.client.login(username="lisa", password="lisa"))

    def test_user_can_update_own_username_with_just_casing_changes(self):
        lisa = TapirUserFactory.create(username="lisa")
        self.login_as_user(lisa)

        response = self.client.post(
            reverse("accounts:edit_username", args=[lisa.id]),
            {"username": "Lisa"},
        )
        self.assertEqual(302, response.status_code)

        lisa.refresh_from_db()
        self.assertEqual("Lisa", lisa.username)
        self.assertTrue(self.client.login(username="Lisa", password="lisa"))

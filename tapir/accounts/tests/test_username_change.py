from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


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

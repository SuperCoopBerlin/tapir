from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestPasswordChange(TapirFactoryTestBase):
    NEW_PASSWORD = "new.password"

    def test_normal_user_can_update_own_password(self):
        normal_user = self.login_as_normal_user()
        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=normal_user.username, password=normal_user.username
            )
        )

        response: TemplateResponse = self.try_update(
            actor=normal_user, target=normal_user
        )
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.assertTrue(
            self.client.login(username=normal_user.username, password=self.NEW_PASSWORD)
        )

    def try_update(self, actor: TapirUser, target: TapirUser):
        self.login_as_user(actor)

        return self.client.post(
            reverse("password_change"),
            {
                "old_password": target.username,
                "new_password1": self.NEW_PASSWORD,
                "new_password2": self.NEW_PASSWORD,
            },
            follow=True,
        )

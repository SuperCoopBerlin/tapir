from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestTapirUserSelfUpdate(TapirFactoryTestBase):
    def test_normal_user_can_self_update(self):
        tapir_user: TapirUser = TapirUserFactory()
        tapir_user.usage_name = "old usage name"
        tapir_user.pronouns = "old pronouns"
        tapir_user.save()
        self.login_as_user(tapir_user)

        response = self.client.post(
            reverse("accounts:user_update_self", args=[tapir_user.id]),
            {
                "usage_name": "new usage name",
                "pronouns": "new pronouns",
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        tapir_user.refresh_from_db()
        self.assertEqual("new usage name", tapir_user.usage_name)
        self.assertEqual("new pronouns", tapir_user.pronouns)

    def test_normal_user_cannot_edit_other_user(self):
        target: TapirUser = TapirUserFactory()
        target.usage_name = "old usage name"
        target.pronouns = "old pronouns"
        target.save()
        actor: TapirUser = TapirUserFactory()
        self.login_as_user(actor)

        response = self.client.post(
            reverse("accounts:user_update_self", args=[target.id]),
            {
                "usage_name": "new usage name",
                "pronouns": "new pronouns",
            },
            follow=True,
        )

        self.assertEqual(403, response.status_code)

        target.refresh_from_db()
        self.assertEqual("old usage name", target.usage_name)
        self.assertEqual("old pronouns", target.pronouns)

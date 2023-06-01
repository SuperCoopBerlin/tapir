from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestTapirUserSelfUpdate(TapirFactoryTestBase):
    def test_normal_user_can_self_update(self):
        actor: TapirUser = TapirUserFactory.create()

        response = self.try_update(actor=actor, target=actor)
        self.assertEqual(200, response.status_code)

        actor.refresh_from_db()
        self.assertEqual("new usage name", actor.usage_name)
        self.assertEqual("new pronouns", actor.pronouns)

    def test_normal_user_cannot_edit_other_user(self):
        target: TapirUser = TapirUserFactory.create()
        actor: TapirUser = TapirUserFactory.create()

        response = self.try_update(actor=actor, target=target)
        self.assertEqual(403, response.status_code)

        target.refresh_from_db()
        self.assertEqual("old usage name", target.usage_name)
        self.assertEqual("old pronouns", target.pronouns)

    def try_update(self, actor: TapirUser, target: TapirUser):
        target.usage_name = "old usage name"
        target.pronouns = "old pronouns"
        target.save()
        self.login_as_user(actor)

        return self.client.post(
            reverse("accounts:user_update_self", args=[target.id]),
            {
                "usage_name": "new usage name",
                "pronouns": "new pronouns",
            },
            follow=True,
        )

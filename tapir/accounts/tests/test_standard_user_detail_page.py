from django.test import Client
from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class AccountsStandardUserDetailPage(TapirFactoryTestBase):
    def test_standard_user_detail_page(self):
        client = Client()
        user: TapirUser = TapirUserFactory.create()
        self.assertTrue(client.login(username=user.username, password=user.username))
        response = client.get(reverse("accounts:user_me"), follow=True)
        self.assertEqual(
            user.id,
            response.context["object"].id,
            "The logged in user should be the view's context object.",
        )
        self.assertInHTML(
            f"<div class='col-12 col-sm-8' id='tapir_user_username'>{ user.username }</div>",
            response.content.decode(),
        )

        for button in [
            "tapir_user_edit_button",
            "share_owner_edit_button",
            "add_note_button",
        ]:
            self.assertNotContains(
                response,
                button,
                200,
                "The user is not in the member office, they should not see the edit buttons",
            )

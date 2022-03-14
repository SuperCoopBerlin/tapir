from django.test import Client
from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class ShiftsStandardUserDetailPage(TapirFactoryTestBase):
    def test_standard_user_detail_page(self):
        client = Client()
        user: TapirUser = TapirUserFactory.create()
        self.assertTrue(client.login(username=user.username, password=user.username))
        response = client.get(reverse("accounts:user_me"), follow=True)

        self.assertContains(
            response,
            "user_shift_card",
            count=1,
            status_code=200,
            msg_prefix="The user shift card should be visible on the member's page",
        )
        for button in [
            "edit_shift_user_data_button",
            "unregister-repeated-shift-button",
        ]:
            self.assertNotContains(
                response,
                button,
                status_code=200,
                msg_prefix="The user is not in the member office, they should not see the edit buttons",
            )

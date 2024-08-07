from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.coop.tests.factories import GeneralAccountFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateGeneralAccount(TapirFactoryTestBase):
    def test_requires_permissions(self):
        self.login_as_normal_user()
        mock_general_account = GeneralAccountFactory.build()

        response = self.visit_view(mock_general_account)

        self.assertEqual(
            response.status_code,
            403,
            "Normal users should not have access to this view.",
        )
        self.assertFalse(
            TapirUser.objects.filter(
                first_name=mock_general_account.first_name,
                last_name=mock_general_account.last_name,
            ).exists(),
            "The general account should not have been created because the logged in user does not have the right permission.",
        )

    def test_create_general_account(self):
        self.login_as_member_office_user()
        mock_general_account = GeneralAccountFactory.build()
        response = self.visit_view(mock_general_account)

        general_accounts = TapirUser.objects.filter(
            first_name=mock_general_account.first_name,
            last_name=mock_general_account.last_name,
        )
        self.assertEqual(
            general_accounts.count(), 1, "The general account should have been created"
        )

        general_account = general_accounts.first()
        self.assertRedirects(response, general_account.get_absolute_url())

        for attribute in GeneralAccountFactory.ATTRIBUTES:
            self.assertEqual(
                getattr(mock_general_account, attribute),
                getattr(general_account, attribute),
                f"The mock general account and the created general account should have the same {attribute}.",
            )

    def visit_view(self, mock_general_account: TapirUser):
        post_data = {}
        for attribute in GeneralAccountFactory.ATTRIBUTES:
            post_data[attribute] = getattr(mock_general_account, attribute)

        return self.client.post(reverse("coop:create_general_account"), post_data)

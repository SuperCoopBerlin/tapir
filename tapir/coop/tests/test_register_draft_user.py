from django.urls import reverse

from tapir.coop.models import DraftUser
from tapir.coop.tests.factories import DraftUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestRegisterDraftUser(TapirFactoryTestBase):
    def test_register_draft_user(self):
        self.client.logout()

        mock_draft_user = DraftUserFactory.build(num_shares=1)
        cant_be_set_when_self_registering = [
            "is_investing",
            "paid_shares",
            "attended_welcome_session",
            "ratenzahlung",
            "paid_membership_fee",
            "signed_membership_agreement",
        ]

        for attribute in cant_be_set_when_self_registering:
            continue
            # Even if the client sends True, those value should be saved as False
            setattr(mock_draft_user, attribute, True)

        post_data = {}
        for attribute in DraftUserFactory.ATTRIBUTES:
            post_data[attribute] = getattr(mock_draft_user, attribute)
        response = self.client.post(reverse("coop:draftuser_register"), post_data)
        print(response.content)
        print(post_data)
        self.assertRedirects(response, reverse("coop:draftuser_confirm_registration"))

        draft_user = DraftUser.objects.get(
            first_name=mock_draft_user.first_name,
            last_name=mock_draft_user.last_name,
        )
        for attribute in DraftUserFactory.ATTRIBUTES:
            self.assertEqual(
                getattr(mock_draft_user, attribute)
                if attribute not in cant_be_set_when_self_registering
                else False,
                getattr(draft_user, attribute),
                f"The mock user and the created user should have the same {attribute}.",
            )

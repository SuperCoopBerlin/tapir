from django.urls import reverse

from tapir.coop.models import DraftUser
from tapir.coop.tests.factories import DraftUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateDraftUser(TapirFactoryTestBase):
    def test_requires_permissions(self):
        self.login_as_normal_user()
        mock_draft_user = DraftUserFactory.build()

        response = self.visit_view(mock_draft_user)

        self.assertEqual(
            response.status_code,
            403,
            "Normal users should not have access to this view.",
        )
        self.assertFalse(
            DraftUser.objects.filter(
                first_name=mock_draft_user.first_name,
                last_name=mock_draft_user.last_name,
            ).exists(),
            "The DraftUser should not have been created because the logged in user does not have the right permission.",
        )

    def test_create_draft_user(self):
        self.login_as_member_office_user()
        mock_draft_user = DraftUserFactory.build(preferred_language="en", country="GB")
        response = self.visit_view(mock_draft_user)

        draft_users = DraftUser.objects.filter(
            first_name=mock_draft_user.first_name,
            last_name=mock_draft_user.last_name,
        )
        self.assertEqual(
            draft_users.count(), 1, "The DraftUser should have been created"
        )

        draft_user = draft_users.first()
        self.assertRedirects(response, draft_user.get_absolute_url())

        for attribute in DraftUserFactory.ATTRIBUTES:
            self.assertEqual(
                getattr(mock_draft_user, attribute),
                getattr(draft_user, attribute),
                f"The mock user and the created user should have the same {attribute}.",
            )

    def visit_view(self, mock_draft_user: DraftUser):
        post_data = {}
        for attribute in DraftUserFactory.ATTRIBUTES:
            post_data[attribute] = getattr(mock_draft_user, attribute)

        return self.client.post(reverse("coop:draftuser_create"), post_data)

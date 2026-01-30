from django.urls import reverse
from django.utils.html import strip_tags


from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShareOwnerUpdateView(TapirFactoryTestBase):
    VIEW_NAME_SHAREOWNER_UPDATE = "coop:shareowner_update"

    def test_shareOwnerUpdateView_loggedInAsNormalUser_notAuthorized(self):
        user = self.login_as_normal_user()
        response = self.client.get(
            reverse(
                self.VIEW_NAME_SHAREOWNER_UPDATE,
                args=[user.share_owner.id],
            )
        )
        self.assertEqual(
            403,
            response.status_code,
            "Normal users should not be allowed to edit member data",
        )

    def test_shareOwnerUpdateView_default_contextDataIsCorrect(self):
        self.login_as_member_office_user(preferred_language="en")
        share_owner = ShareOwnerFactory.create(
            first_name="Hyper", usage_name="Super", last_name="Coop"
        )
        response = self.client.get(
            reverse(
                self.VIEW_NAME_SHAREOWNER_UPDATE,
                args=[share_owner.id],
            )
        )
        self.assertEqual(
            200,
            response.status_code,
            "Member office users should be able to access this page",
        )
        self.assertEqual(
            f"Edit member: Super Coop #{share_owner.id}",
            response.context_data["page_title"],
        )
        self.assertEqual(
            f"Edit member: Super Coop #{share_owner.id}",
            strip_tags(response.context_data["card_title"]),
        )

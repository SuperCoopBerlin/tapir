from django.urls import reverse
from icecream import ic

from tapir.coop.tests.factories import DraftUserFactory, ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestDraftUserDetailView(TapirFactoryTestBase):
    def test_requires_permissions(self):
        self.login_as_normal_user()
        draft_user = DraftUserFactory.create()

        response = self.client.get(
            reverse("coop:draftuser_detail", args=[draft_user.id])
        )

        self.assertEqual(
            response.status_code,
            403,
            "Normal users should not have access to this view.",
        )

    def test_shows_similar_members(self):
        self.login_as_member_office_user()
        last_name = "test last name"
        phone_number = "+49 176 26 25 43 36"
        street = "test street"
        email = "test@mail.net"
        draft_user = DraftUserFactory.create(
            last_name=last_name, phone_number=phone_number, street=street, email=email
        )
        so1 = ShareOwnerFactory.create(last_name=last_name)
        so2 = ShareOwnerFactory.create(phone_number=phone_number)
        so3 = ShareOwnerFactory.create(street=street)
        so4 = ShareOwnerFactory.create(email=email)

        response = self.client.get(
            reverse("coop:draftuser_detail", args=[draft_user.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual([so1, so2, so3, so4], response.context["similar_members"])

    def test_members_without_phone_number_are_not_shown(self):
        self.login_as_member_office_user()

        last_name = "test last name"
        draft_user = DraftUserFactory.create(last_name=last_name, phone_number="")
        share_owner_1 = ShareOwnerFactory.create(last_name=last_name, phone_number="")
        share_owner_2 = ShareOwnerFactory.create(
            last_name="other last name", phone_number=""
        )

        response = self.client.get(
            reverse("coop:draftuser_detail", args=[draft_user.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(share_owner_1, response.context["similar_members"])
        self.assertNotIn(share_owner_2, response.context["similar_members"])

    def test_members_without_address_are_not_shown(self):
        self.login_as_member_office_user()

        last_name = "test last name"
        draft_user = DraftUserFactory.create(last_name=last_name, street="")
        share_owner_1 = ShareOwnerFactory.create(last_name=last_name, street="")
        share_owner_2 = ShareOwnerFactory.create(last_name="other last name", street="")

        response = self.client.get(
            reverse("coop:draftuser_detail", args=[draft_user.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(share_owner_1, response.context["similar_members"])
        self.assertNotIn(share_owner_2, response.context["similar_members"])

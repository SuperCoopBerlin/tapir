from django.core import mail
from django.core.exceptions import ValidationError
from django.urls import reverse

from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.emails.membership_confirmation_email_for_active_member import (
    MembershipConfirmationForActiveMemberEmail,
)
from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
    MembershipConfirmationForInvestingMemberEmail,
)
from tapir.coop.models import DraftUser, ShareOwner, ShareOwnership
from tapir.coop.tests.factories import DraftUserFactory, ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase


class TestsDraftUserToShareOwner(TapirFactoryTestBase, TapirEmailTestBase):
    VIEW_NAME = "coop:draftuser_create_share_owner"
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_requires_permissions(self):
        self.login_as_normal_user()
        draft_user = DraftUserFactory.create(signed_membership_agreement=True)
        response = self.client.post(reverse(self.VIEW_NAME, args=[draft_user.pk]))

        self.assertIn(
            reverse("login"),
            response.url,
            "The user should be redirected to the login page because they don't have the right permissions",
        )  # Can't use self.assertRedirects because the response's URL contains the get parameters
        self.assertFalse(
            ShareOwner.objects.filter(
                first_name=draft_user.first_name, last_name=draft_user.last_name
            ).exists(),
            "The ShareOwner should not have been created because the logged in user does not have the right permission",
        )

    def test_draft_user_to_share_owner(self):
        self.login_as_member_office_user()

        draft_user = DraftUserFactory.create(signed_membership_agreement=True)
        response = self.client.post(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        share_owners = ShareOwner.objects.filter(
            first_name=draft_user.first_name, last_name=draft_user.last_name
        )
        self.assertEqual(
            share_owners.count(), 1, "The share owner should have been created"
        )

        share_owner = share_owners.first()
        self.assertRedirects(
            response,
            share_owner.get_absolute_url(),
            msg_prefix="The user should be redirected to the new member's page",
        )
        self.assertFalse(
            DraftUser.objects.filter(
                first_name=draft_user.first_name, last_name=draft_user.last_name
            ).exists(),
            "After creating the share owner, the draft user should have been destroyed",
        )

        for attribute in ShareOwnerFactory.ATTRIBUTES:
            self.assertEqual(
                getattr(draft_user, attribute),
                getattr(share_owner, attribute),
                f"The DraftUser and the ShareOwner should have the same {attribute}",
            )

        self.assertEqual(
            ShareOwnership.objects.filter(owner=share_owner).count(),
            draft_user.num_shares,
            "The ShareOwner should have the number of shares requested by the DraftUser",
        )

    def test_share_owner_creation_needs_signed_membership_agreement(self):
        self.login_as_member_office_user()

        draft_user = DraftUserFactory.create(signed_membership_agreement=False)
        with self.assertRaises(ValidationError):
            self.client.post(reverse(self.VIEW_NAME, args=[draft_user.pk]))

    def test_paid_shares(self):
        self.login_as_member_office_user()

        for paid_shares in [True, False]:
            draft_user = DraftUserFactory.create(
                signed_membership_agreement=True, paid_shares=paid_shares
            )
            self.client.post(reverse(self.VIEW_NAME, args=[draft_user.pk]))
            share_owner = ShareOwner.objects.get(
                first_name=draft_user.first_name, last_name=draft_user.last_name
            )
            amount_paid = COOP_SHARE_PRICE if paid_shares else 0
            self.assertEqual(
                ShareOwnership.objects.filter(
                    owner=share_owner, amount_paid=amount_paid
                ).count(),
                draft_user.num_shares,
                "The created shares should not be paid",
            )

    def test_creating_active_share_owner_sends_the_membership_confirmation_for_active_members_email(
        self,
    ):
        self.login_as_member_office_user()

        draft_user = DraftUserFactory.create(
            signed_membership_agreement=True,
            is_investing=False,
            email=self.USER_EMAIL_ADDRESS,
        )
        self.assertEqual(0, len(mail.outbox))
        self.client.post(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            MembershipConfirmationForActiveMemberEmail,
            self.USER_EMAIL_ADDRESS,
            mail.outbox[0],
        )

    def test_creating_investing_share_owner_sends_the_membership_confirmation_for_investing_members_email(
        self,
    ):
        self.login_as_member_office_user()

        draft_user = DraftUserFactory.create(
            signed_membership_agreement=True,
            is_investing=True,
            email=self.USER_EMAIL_ADDRESS,
        )
        self.assertEqual(0, len(mail.outbox))
        self.client.post(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            MembershipConfirmationForInvestingMemberEmail,
            self.USER_EMAIL_ADDRESS,
            mail.outbox[0],
        )

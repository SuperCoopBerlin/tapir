from django.contrib.messages import get_messages
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.emails.membership_confirmation_email_for_active_member import (
    MembershipConfirmationForActiveMemberEmailBuilder,
)
from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
    MembershipConfirmationForInvestingMemberEmailBuilder,
)
from tapir.coop.models import (
    ShareOwner,
    ShareOwnership,
    NewMembershipsForAccountingRecap,
    DraftUser,
)
from tapir.coop.tests.factories import DraftUserFactory, ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class TestsDraftUserToShareOwner(TapirFactoryTestBase, TapirEmailTestMixin):
    VIEW_NAME = "coop:draftuser_create_share_owner"
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_requires_permissions(self):
        self.login_as_normal_user()
        draft_user = DraftUserFactory.create(signed_membership_agreement=True)
        response = self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))

        self.assertEqual(
            403,
            response.status_code,
            "A normal user should not have access to this call",
        )
        self.assertFalse(
            ShareOwner.objects.filter(
                first_name=draft_user.first_name, last_name=draft_user.last_name
            ).exists(),
            "The ShareOwner should not have been created because the logged in user does not have the right permission",
        )

    def test_draft_user_to_share_owner(self):
        self.login_as_member_office_user()

        draft_user = DraftUserFactory.create(signed_membership_agreement=True)
        response = self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        share_owners = ShareOwner.objects.filter(
            first_name=draft_user.first_name, last_name=draft_user.last_name
        )
        self.assertEqual(
            share_owners.count(), 1, "The shareowner should have been created"
        )

        share_owner = share_owners.first()
        self.assertRedirects(
            response,
            share_owner.get_absolute_url(),
            msg_prefix="The user should be redirected to the new member's page",
        )
        draft_user.refresh_from_db()
        self.assertEqual(
            share_owner,
            draft_user.share_owner,
            "After creating the share_owner, the corresponding field on DraftUser should be set to the correct value",
        )

        for attribute in ShareOwnerFactory.ATTRIBUTES:
            self.assertEqual(
                getattr(draft_user, attribute),
                getattr(share_owner, attribute),
                f"The DraftUser and the ShareOwner should have the same {attribute}",
            )

        self.assertEqual(
            ShareOwnership.objects.filter(share_owner=share_owner).count(),
            draft_user.num_shares,
            "The ShareOwner should have the number of shares requested by the DraftUser",
        )

    def test_share_owner_creation_needs_signed_membership_agreement(self):
        self.login_as_member_office_user()
        draft_user: DraftUser = DraftUserFactory.create(
            signed_membership_agreement=False
        )

        response = self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        self.assertRedirects(
            response,
            draft_user.get_absolute_url(),
            msg_prefix="The user should be redirect to the draft_user's page.",
        )
        messages = get_messages(response.wsgi_request)
        self.assertEqual(
            1,
            len(messages),
            "An error message should be shown on the draft_user's page.",
        )

    def test_paid_shares(self):
        self.login_as_member_office_user()

        for paid_shares in [True, False]:
            draft_user = DraftUserFactory.create(
                signed_membership_agreement=True, paid_shares=paid_shares
            )
            self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))
            share_owner = ShareOwner.objects.get(
                first_name=draft_user.first_name, last_name=draft_user.last_name
            )
            amount_paid = COOP_SHARE_PRICE if paid_shares else 0
            self.assertEqual(
                ShareOwnership.objects.filter(
                    share_owner=share_owner, amount_paid=amount_paid
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
        self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            MembershipConfirmationForActiveMemberEmailBuilder,
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
        self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            MembershipConfirmationForInvestingMemberEmailBuilder,
            self.USER_EMAIL_ADDRESS,
            mail.outbox[0],
        )

    def test_creating_a_share_owner_creates_a_recap_entry(self):
        self.login_as_member_office_user()
        draft_user = DraftUserFactory.create(
            signed_membership_agreement=True, num_shares=3
        )

        self.assertEqual(0, NewMembershipsForAccountingRecap.objects.count())
        self.client.get(reverse(self.VIEW_NAME, args=[draft_user.pk]))
        self.assertEqual(1, NewMembershipsForAccountingRecap.objects.count())
        recap_entry = NewMembershipsForAccountingRecap.objects.all()[0]
        self.assertEqual(draft_user.first_name, recap_entry.member.first_name)
        self.assertEqual(timezone.now().date(), recap_entry.date)
        self.assertEqual(3, recap_entry.number_of_shares)

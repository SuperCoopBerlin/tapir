from django.core import mail
from django.urls import reverse

from tapir.coop.emails.membership_confirmation_email_for_active_member import (
    MembershipConfirmationForActiveMemberEmail,
)
from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
    MembershipConfirmationForInvestingMemberEmail,
)
from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase


class TestSendMembershipConfirmationEmail(TapirFactoryTestBase, TapirEmailTestBase):
    VIEW_NAME = "coop:send_shareowner_membership_confirmation_welcome_email"
    USER_EMAIL_ADDRESS = "test_address@test.net"

    def test_requires_permissions(self):
        normal_user = self.login_as_normal_user()
        response = self.client.post(
            reverse(
                self.VIEW_NAME,
                args=[normal_user.share_owner.pk],
            ),
            follow=False,
        )

        self.assertIn(
            reverse("login"),
            response.url,
            "The user should be redirected to the login page because they don't have the right permissions",
        )
        self.assertEqual(0, len(mail.outbox))

    def test_sends_correct_mail_to_active_member(self):
        active_member: ShareOwner = ShareOwnerFactory.create(
            is_investing=False, email=self.USER_EMAIL_ADDRESS
        )
        self.login_as_member_office_user()

        self.assertEqual(0, len(mail.outbox))
        self.client.post(
            reverse(
                self.VIEW_NAME,
                args=[active_member.pk],
            ),
        )
        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            MembershipConfirmationForActiveMemberEmail,
            self.USER_EMAIL_ADDRESS,
            sent_mail,
        )
        self.assertEqual(1, len(sent_mail.attachments))
        self.assertEmailAttachmentIsAPdf(sent_mail.attachments[0])

    def test_sends_correct_mail_to_investing_member(self):
        active_member: ShareOwner = ShareOwnerFactory.create(
            is_investing=True, email=self.USER_EMAIL_ADDRESS
        )
        self.login_as_member_office_user()

        self.assertEqual(0, len(mail.outbox))
        self.client.post(
            reverse(
                self.VIEW_NAME,
                args=[active_member.pk],
            ),
        )
        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            MembershipConfirmationForInvestingMemberEmail,
            self.USER_EMAIL_ADDRESS,
            sent_mail,
        )
        self.assertEqual(1, len(sent_mail.attachments))
        self.assertEmailAttachmentIsAPdf(sent_mail.attachments[0])

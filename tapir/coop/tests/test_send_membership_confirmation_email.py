from django.core import mail
from django.urls import reverse

from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSendMembershipConfirmationEmail(TapirFactoryTestBase):
    VIEW_NAME = "coop:send_shareowner_membership_confirmation_welcome_email"

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
        active_member: ShareOwner = ShareOwnerFactory.create(is_investing=False)
        self.login_as_member_office_user()

        self.assertEqual(0, len(mail.outbox))
        self.client.post(
            reverse(
                self.VIEW_NAME,
                args=[active_member.pk],
            ),
        )
        self.assertEqual(1, len(mail.outbox))
        self.assertNotIn("investing", mail.outbox[0].body)

    def test_sends_correct_mail_to_investing_member(self):
        active_member: ShareOwner = ShareOwnerFactory.create(is_investing=True)
        self.login_as_member_office_user()

        self.assertEqual(0, len(mail.outbox))
        self.client.post(
            reverse(
                self.VIEW_NAME,
                args=[active_member.pk],
            ),
        )
        self.assertEqual(1, len(mail.outbox))
        self.assertIn("investing", mail.outbox[0].body)

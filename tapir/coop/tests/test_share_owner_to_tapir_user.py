from django.core import mail
from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase


class TestsShareOwnerToTapirUser(TapirFactoryTestBase, TapirEmailTestBase):
    def test_requires_permissions(self):
        self.login_as_normal_user()
        share_owner: ShareOwner = ShareOwnerFactory.create()
        response = self.visit_create_user_view(share_owner)

        self.assertEqual(
            response.status_code,
            403,
            "The user should not be allowed to use this view because they don't have the right permissions",
        )
        self.assertFalse(
            TapirUser.objects.filter(share_owner=share_owner).exists(),
            "The TapirUser should not have been created because the logged in user does not have the right permission",
        )

    def test_share_owner_to_tapir_user(self):
        share_owner: ShareOwner = ShareOwnerFactory.create()
        self.login_as_member_office_user()
        response = self.visit_create_user_view(share_owner)

        tapir_users = TapirUser.objects.filter(share_owner=share_owner)
        self.assertEqual(tapir_users.count(), 1, "The user should have been created.")
        tapir_user = tapir_users.first()

        self.assertRedirects(
            response,
            tapir_user.get_absolute_url(),
            msg_prefix="The user should be redirected to the new TapirUser's page.",
        )

        for attribute in UserDataFactory.ATTRIBUTES:
            self.assertEqual(
                getattr(share_owner, attribute),
                getattr(tapir_user, attribute),
                f"The ShareOwner and the TapirUser should have the same {attribute}.",
            )

        share_owner = tapir_user.share_owner
        for attribute in UserDataFactory.ATTRIBUTES:
            self.assertFalse(
                getattr(share_owner, attribute),
                f"The ShareOwner should have his {attribute} blanked.",
            )

        tapir_user.set_password(tapir_user.username)
        self.login_as_user(
            tapir_user
        )  # Assert if login is successful is done in login_as_user

    def test_cant_create_company(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(is_company=True)
        self.login_as_member_office_user()
        response = self.visit_create_user_view(share_owner)

        self.assertEqual(
            response.status_code,
            403,
            "It should not be possible to create a TapirUser for companies",
        )
        self.assertFalse(
            TapirUser.objects.filter(share_owner=share_owner).exists(),
            "The TapirUser should not have been created.",
        )

    def test_cant_create_user_already_exists(self):
        tapir_user = TapirUserFactory.create()
        self.login_as_member_office_user()
        response = self.visit_create_user_view(tapir_user.share_owner)

        self.assertEqual(
            response.status_code,
            403,
            "It should not be possible to create a TapirUser from a ShareOwner that already has a TapirUser",
        )
        self.assertEqual(
            TapirUser.objects.filter(share_owner=tapir_user.share_owner).count(),
            1,
            "Only the original TapirUser should be there, the request should not have created an extra user.",
        )

    def test_creating_the_user_must_send_the_activation_email(self):
        user_email_address = "test_address@test.net"
        share_owner: ShareOwner = ShareOwnerFactory.create(email=user_email_address)
        self.login_as_member_office_user()

        self.assertEqual(len(mail.outbox), 0)
        self.visit_create_user_view(share_owner)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            TapirAccountCreatedEmail, user_email_address, sent_mail
        )
        self.assertIn(
            TapirUser.objects.all().last().username,
            sent_mail.body,
            "The username must be included in the email",
        )

    def visit_create_user_view(self, share_owner: ShareOwner):
        return self.client.post(
            reverse("coop:create_user_from_shareowner", args=[share_owner.pk]),
            {
                "first_name": share_owner.get_info().first_name,
                "usage_name": share_owner.get_info().usage_name,
                "last_name": share_owner.get_info().last_name,
                "username": f"{share_owner.get_info().first_name.lower()}.{share_owner.get_info().last_name.lower()}",
            },
        )

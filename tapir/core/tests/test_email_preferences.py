from tapir.accounts.models import TapirUser, OptionalMails
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.utils.tests_utils import TapirFactoryTestBase

from django.urls import reverse


class OptionalNonDefaultMail(TapirEmailBase):
    optional = True
    enabled_by_default = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.OptionalNonDefaultMail"

    @classmethod
    def get_name(cls) -> str:
        return "OptionalNonDefaultMail"


class MandatoryMail(TapirEmailBase):
    optional = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.MandatoryMail"

    @classmethod
    def get_name(cls) -> str:
        return "MandatoryMail"


class TestMailSetting(TapirFactoryTestBase):
    def setUp(self):
        TapirEmailBase.register_email(OptionalNonDefaultMail)

    def test_userWantsToOrHasToReceiveMail_mailNotSubscribedTo_shouldNotReceiveMail(
        self,
    ):
        assert OptionalNonDefaultMail.enabled_by_default == False
        tapir_user: TapirUser = TapirUserFactory.create()
        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def test_userWantsToOrHasToReceiveMail_mailSubscribedTo_shouldReceiveMail(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        OptionalMails.objects.create(
            user=tapir_user, mail_id=OptionalNonDefaultMail.get_unique_id(), choice=True
        )
        self.assertTrue(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def send_request_add_OptionalNonDefaultMail_to_subscribed_mails(
        self, usr: TapirUser
    ):
        post_data = {"optional_mails": [OptionalNonDefaultMail.get_unique_id()]}
        response = self.client.post(
            reverse("accounts:mail_settings", args=[usr.pk]),
            post_data,
            follow=True,
        )
        return response

    def test_normalUser_CannotAccessOtherUsersMailSettings(self):
        tapir_user = TapirUserFactory()
        actor = TapirUserFactory()
        self.login_as_user(actor)
        response = self.client.get(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
        )

        self.assertEqual(403, response.status_code)

    def test_NormalUser_CannotUpdateOtherUsersMailSettings(self):
        tapir_user = TapirUserFactory()
        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

        self.login_as_user(TapirUserFactory())
        self.send_request_add_OptionalNonDefaultMail_to_subscribed_mails(tapir_user)
        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def test_NormalUser_AccessOwnMailSettings_returnsStatus200(self):
        tapir_user = TapirUserFactory()
        self.login_as_user(tapir_user)
        response = self.client.get(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
        )
        self.assertTrue(200, response.status_code)

    def test_NormalUser_UpdateOwnMailSetting_returnsTrue(self):
        tapir_user = TapirUserFactory()
        self.login_as_user(tapir_user)

        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

        response = self.send_request_add_OptionalNonDefaultMail_to_subscribed_mails(
            tapir_user
        )
        self.assertEqual(200, response.status_code)

        tapir_user.refresh_from_db()
        self.assertTrue(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def test_MemberOffice_canUpdateOtherUsersMailSettings_returnsTrue(self):
        tapir_user = TapirUserFactory()
        self.login_as_member_office_user()

        response = self.send_request_add_OptionalNonDefaultMail_to_subscribed_mails(
            usr=tapir_user
        )
        self.assertEqual(200, response.status_code)

        tapir_user.refresh_from_db()
        self.assertTrue(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def test_NormalUser_CannotUpdateNonOptionalMailSettings(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        self.login_as_user(tapir_user)
        # Enabled by default and mandatory
        self.assertTrue(
            MandatoryMail().user_wants_to_or_has_to_receive_mail(user=tapir_user)
        )

        post_data = {"mandatory_mails": []}
        self.client.post(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
            post_data,
            follow=True,
        )
        tapir_user.refresh_from_db()
        self.assertTrue(
            MandatoryMail().user_wants_to_or_has_to_receive_mail(user=tapir_user)
        )

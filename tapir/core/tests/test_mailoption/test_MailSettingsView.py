from http import HTTPStatus

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.core.tapir_email_base import MailOption, TapirEmailBase
from tapir.utils.tests_utils import TapirFactoryTestBase

from django.urls import reverse


class OptionalNonDefaultMail(TapirEmailBase):
    option = MailOption.OPTIONAL_DISABLED

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.OptionalNonDefaultMail"

    @classmethod
    def get_name(cls) -> str:
        return "OptionalNonDefaultMail"


class MandatoryMail(TapirEmailBase):
    option = MailOption.MANDATORY

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.MandatoryMail"

    @classmethod
    def get_name(cls) -> str:
        return "MandatoryMail"


def setup_mails():
    TapirEmailBase.register_email(OptionalNonDefaultMail)
    TapirEmailBase.register_email(MandatoryMail)


class TestMailSettingView(TapirFactoryTestBase):
    def setUp(self):
        setup_mails()

    def test_permission_NormalUser_canUpdateOwnMailSetting(self):
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
        self.assertStatusCode(response=response, expected_status_code=HTTPStatus.OK)

        tapir_user.refresh_from_db()
        self.assertTrue(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def test_permissions_MemberOffice_canUpdateOtherUsersMailSettings(self):
        tapir_user = TapirUserFactory()
        self.login_as_member_office_user()

        response = self.send_request_add_OptionalNonDefaultMail_to_subscribed_mails(
            usr=tapir_user
        )
        self.assertStatusCode(response=response, expected_status_code=HTTPStatus.OK)

        tapir_user.refresh_from_db()
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

    def test_permissions_normalUser_cannotAccessOtherUsersMailSettings(self):
        tapir_user = TapirUserFactory()
        actor = TapirUserFactory()
        self.login_as_user(actor)
        response = self.client.get(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
        )

        self.assertStatusCode(
            response=response, expected_status_code=HTTPStatus.FORBIDDEN
        )

    def test_permissions_NormalUser_CannotUpdateOtherUsersMailSettings(self):
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

    def test_permissions_NormalUser_canAccessOwnMailSettings(self):
        tapir_user = TapirUserFactory()
        self.login_as_user(tapir_user)
        response = self.client.get(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
        )
        self.assertStatusCode(response=response, expected_status_code=HTTPStatus.OK)

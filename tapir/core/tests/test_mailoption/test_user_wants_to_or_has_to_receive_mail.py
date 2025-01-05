from django.urls import reverse

from tapir.accounts.models import TapirUser, OptionalMails
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.core.tapir_email_base import MailOption
from tapir.core.tests.test_mailoption.test_MailSettingsView import (
    MandatoryMail,
    OptionalNonDefaultMail,
    setup_mails,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestUserWantsToOrHasToReceiveMail(TapirFactoryTestBase):
    def setUp(self):
        setup_mails()

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

    def test_userWantsToOrHasToReceiveMail_mailNotSubscribedTo_shouldNotReceiveMail(
        self,
    ):
        assert OptionalNonDefaultMail.option == MailOption.OPTIONAL_DISABLED
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

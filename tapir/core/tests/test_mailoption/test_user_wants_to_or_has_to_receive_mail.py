from django.urls import reverse

from tapir.accounts.models import TapirUser, OptionalMails
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.core.mail_option import MailOption
from tapir.core.services.optional_mails_for_user_service import (
    OptionalMailsForUserService,
)
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
            OptionalMailsForUserService.user_wants_to_or_has_to_receive_mail(
                user=tapir_user, mail_class=MandatoryMail
            )
        )

        post_data = {"mandatory_mails": []}
        self.client.post(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
            post_data,
            follow=True,
        )
        tapir_user.refresh_from_db()
        self.assertTrue(
            OptionalMailsForUserService.user_wants_to_or_has_to_receive_mail(
                user=tapir_user, mail_class=MandatoryMail
            )
        )

    def test_userWantsToOrHasToReceiveMail_mailNotSubscribedTo_shouldNotReceiveMail(
        self,
    ):
        assert OptionalNonDefaultMail.option == MailOption.OPTIONAL_DISABLED
        tapir_user: TapirUser = TapirUserFactory.create()
        self.assertFalse(
            OptionalMailsForUserService.user_wants_to_or_has_to_receive_mail(
                user=tapir_user, mail_class=OptionalNonDefaultMail
            )
        )

    def test_userWantsToOrHasToReceiveMail_mailSubscribedTo_shouldReceiveMail(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        OptionalMails.objects.create(
            user=tapir_user, mail_id=OptionalNonDefaultMail.get_unique_id(), choice=True
        )
        self.assertTrue(
            OptionalMailsForUserService.user_wants_to_or_has_to_receive_mail(
                user=tapir_user, mail_class=OptionalNonDefaultMail
            )
        )

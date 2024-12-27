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
        return "tapir.coop.voluntaryTestMail"

    @classmethod
    def get_name(cls) -> str:
        return "VoluntaryTestMail"


class TestOptionalNotDefaultMail(TapirFactoryTestBase):
    def setUp(self):
        TapirEmailBase.register_email(OptionalNonDefaultMail)

    def test_userWantsToOrHasToReceiveMail_mailNotSubscribedTo_shouldNotReceiveMail(
        self,
    ):
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

    def test_userWantsToOrHasToReceiveMail_NotSubscribedTo_shouldNotReceiveMail(
        self,
    ):
        OptionalNonDefaultMail.enabled_by_default = False
        tapir_user: TapirUser = TapirUserFactory.create()

        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )


class TestMailSetting(TapirFactoryTestBase):
    def setUp(self):
        TapirEmailBase.register_email(OptionalNonDefaultMail)

    def test_normal_user_cant_access_mail_setting(self):
        tapir_user = TapirUserFactory()
        actor = TapirUserFactory()
        self.login_as_user(actor)
        response = self.client.get(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
        )

        self.assertEqual(403, response.status_code)
        # tapir_user.refresh_from_db()
        # self.assertEqual(False, tapir_user.allows_purchase_tracking)

    def test_normal_user_cannot_update_other_users_mail_setting(self):
        tapir_user = TapirUserFactory()
        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

        actor = TapirUserFactory()
        self.login_as_user(actor)
        self.client.post(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
            {"optional_mails": OptionalNonDefaultMail.get_unique_id()},
            follow=True,
        )
        self.assertFalse(
            OptionalNonDefaultMail().user_wants_to_or_has_to_receive_mail(
                user=tapir_user
            )
        )

    def test_user_can_access_own_settings(self):
        tapir_user = TapirUserFactory()
        self.login_as_user(tapir_user)
        response = self.client.get(
            reverse("accounts:mail_settings", args=[tapir_user.pk]),
        )
        self.assertTrue(200, response.status_code)

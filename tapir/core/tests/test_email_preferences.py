from tapir.accounts.models import TapirUser, OptionalMails, MailChoice
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.utils.tests_utils import TapirFactoryTestBase


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
        m = MailChoice.objects.create(
            name=OptionalNonDefaultMail.get_unique_id(), choice=True
        )
        OptionalMails.objects.create(user=tapir_user, mail=m)
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

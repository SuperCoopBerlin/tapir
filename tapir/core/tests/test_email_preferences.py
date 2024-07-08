from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.utils.tests_utils import TapirFactoryTestBase


class VoluntaryMail(TapirEmailBase):
    mandatory = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.voluntaryTestMail"

    @classmethod
    def get_name(cls) -> str:
        return "VoluntaryTestMail"


class TestVoluntaryMails(TapirFactoryTestBase):
    def setUp(self):
        TapirEmailBase.register_email(VoluntaryMail)

    def test_userWantsToOrHasToReceiveMail_mailNotSubscribedTo_shouldNotReceiveMail(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()

        self.assertTrue(
            VoluntaryMail().user_wants_to_or_has_to_receive_mail(user=tapir_user)
            is False
        )

    def test_userWantsToOrHasToReceiveMail_mailSubscribedTo_shouldReceiveMail(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.additional_mails = ["tapir.coop.voluntaryTestMail"]

        self.assertTrue(
            VoluntaryMail().user_wants_to_or_has_to_receive_mail(user=tapir_user)
        )

    def test_userWantsToOrHasToReceiveMail_mailIsMandatory_shouldReceiveMail(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        self.assertTrue(
            TapirAccountCreatedEmail.mandatory
        )  # change to another mail-type if necessary

        self.assertTrue(
            TapirAccountCreatedEmail(
                tapir_user=tapir_user
            ).user_wants_to_or_has_to_receive_mail(user=tapir_user)
        )

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.utils.tests_utils import LdapEnabledTestCase


class VoluntaryMail(TapirEmailBase):
    mandatory = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.voluntaryTestMail"

    @classmethod
    def get_name(cls) -> str:
        return "VoluntaryTestMail"


class TestVoluntaryMails(LdapEnabledTestCase):
    def setUp(self):
        TapirEmailBase.register_email(VoluntaryMail)

    def test_has_voluntary_mail_NOT_subscribed(self):
        tapir_user: TapirUser = TapirUserFactory.create()

        assert (
            VoluntaryMail().user_wants_to_or_has_to_receive_mail(user=tapir_user)
            is False
        )

    def test_has_voluntary_mail_subscribed(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.additional_mails = ["tapir.coop.voluntaryTestMail"]

        assert VoluntaryMail().user_wants_to_or_has_to_receive_mail(user=tapir_user)

    def test_has_mandatory_mail_subscribed(self):
        tapir_user: TapirUser = TapirUserFactory.create()
        assert (
            TapirAccountCreatedEmail.mandatory
        )  # change to another mail-type if necessary

        assert TapirAccountCreatedEmail(
            tapir_user=tapir_user
        ).user_wants_to_or_has_to_receive_mail(user=tapir_user)

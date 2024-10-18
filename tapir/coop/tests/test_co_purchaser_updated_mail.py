from django.core import mail
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.emails.co_purchaser_updated_mail import CoPurchaserUpdatedMail
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class TestCoPurchaserUpdatedMail(TapirFactoryTestBase, TapirEmailTestMixin):
    def test_setCoPurchaserToBlank_noEmailSent(self):
        self.login_as_member_office_user()
        tapir_user = TapirUserFactory.create(co_purchaser="A test co-purchaser")

        response = self.client.post(
            reverse("accounts:user_update", args=[tapir_user.id]),
            data={
                "co_purchaser": "",
                "preferred_language": tapir_user.preferred_language,
                "username": tapir_user.username,
                "email": tapir_user.email,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:user_detail", args=[tapir_user.id]),
            msg_prefix=f"If the redirection is not to the user's page, the request got probably rejected: {response.content.decode()}",
        )
        tapir_user.refresh_from_db()
        self.assertEqual("", tapir_user.co_purchaser)
        self.assertEqual(0, len(mail.outbox))

    def test_setCoPurchaserToNotBlank_emailSent(self):
        self.login_as_member_office_user()
        tapir_user = TapirUserFactory.create(co_purchaser="Old co-purchased")
        co_purchaser_name = "A test co-purchaser"

        response = self.client.post(
            reverse("accounts:user_update", args=[tapir_user.id]),
            data={
                "co_purchaser": co_purchaser_name,
                "preferred_language": tapir_user.preferred_language,
                "username": tapir_user.username,
                "email": tapir_user.email,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:user_detail", args=[tapir_user.id]),
            msg_prefix=f"If the redirection is not to the user's page, the request got probably rejected: {response.content.decode()}",
        )
        tapir_user.refresh_from_db()
        self.assertEqual(co_purchaser_name, tapir_user.co_purchaser)
        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            CoPurchaserUpdatedMail,
            tapir_user.email,
            sent_mail,
        )
        self.assertIn(co_purchaser_name, sent_mail.body)

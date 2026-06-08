from django.core import mail
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.config import feature_flag_buy_shares
from tapir.coop.emails.extra_shares_buy_mail import ExtraSharesBuyEmailBuilder
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirEmailTestMixin,
    TapirFactoryTestBase,
)


class TestCreateExtraShares(
    FeatureFlagTestMixin, TapirFactoryTestBase, TapirEmailTestMixin
):
    VIEW_NAME = "coop:share_create"

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_buy_shares, True)

    def test_buyShares_asMemberOfficeForAnotherUser_fails(self):
        self.login_as_member_office_user()

        email_address = "test_address@test.net"
        tapir_user = TapirUserFactory(email=email_address)

        num_shares = 3
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.share_owner.id]),
            {
                "num_shares": num_shares,
                "participation_confirm": "on",
                "statutes_acknowledged": "on",
                "termination_period_accepted": "on",
            },
        )
        self.assertEqual(
            response.status_code,
            403,
            "A member office user should not be able to create shares.",
        )

    def test_buyShares_asVorstandForAnotherUser_fails(self):
        user = self.login_as_vorstand()
        email_address = "test_address@test.net"
        tapir_user = TapirUserFactory(email=email_address)

        num_shares = 3
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.share_owner.id]),
            {
                "num_shares": num_shares,
                "participation_confirm": "on",
                "statutes_acknowledged": "on",
                "termination_period_accepted": "on",
            },
        )
        self.assertEqual(
            response.status_code,
            403,
            "A member office user should not be able to create shares.",
        )

    def test_buyShares_formFilledCorrectly_sendsTwoEmails(self):
        email_address = "test_address@test.net"
        tapir_user = TapirUserFactory(email=email_address)

        num_shares = 3
        self.login_as_user(tapir_user)

        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.share_owner.id]),
            {
                "num_shares": num_shares,
                "participation_confirm": "on",
                "statutes_acknowledged": "on",
                "termination_period_accepted": "on",
            },
        )

        self.assertEqual(len(mail.outbox), 2)
        mail_to_member_office = mail.outbox[0]
        mail_to_user = mail.outbox[1]
        self.assertEmailOfClass_GotSentTo(
            ExtraSharesBuyEmailBuilder, email_address, mail_to_user
        )

        self.assertEqual(1, len(mail_to_user.attachments))
        self.assertEqual(1, len(mail_to_member_office.attachments))

        self.assertEmailAttachmentIsAPdf(mail_to_user.attachments[0])
        self.assertEmailAttachmentIsAPdf(mail_to_member_office.attachments[0])

    def test_buyShares_withoutConsent_throwsStatusCode302(self):
        email_address = "test_address@test.net"
        tapir_user = TapirUserFactory(email=email_address)

        num_shares = 3
        self.login_as_user(tapir_user)

        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.share_owner.id]),
            {
                "num_shares": num_shares,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_buyShares_getWithFeatureDisabled_returnsForbidden(self):
        """Test that status endpoint returns 302 when feature flag is disabled."""
        self.given_feature_flag_value(feature_flag_buy_shares, False)

        email_address = "test_address@test.net"
        tapir_user = TapirUserFactory(email=email_address)

        num_shares = 3
        self.login_as_user(tapir_user)

        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.share_owner.id]),
            {
                "num_shares": num_shares,
                "participation_confirm": "on",
                "statutes_acknowledged": "on",
                "termination_period_accepted": "on",
            },
        )
        self.assertStatusCode(response, 302)

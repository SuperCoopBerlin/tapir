import datetime

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from tapir.coop.emails.extra_shares_confirmation_email import (
    ExtraSharesConfirmationEmail,
)
from tapir.coop.models import (
    CreateShareOwnershipsLogEntry,
    ShareOwner,
    ExtraSharesForAccountingRecap,
)
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase


class TestCreateExtraShares(TapirFactoryTestBase, TapirEmailTestBase):
    VIEW_NAME = "coop:share_create_multiple"

    def test_create_shares_requires_permissions(self):
        user = self.login_as_normal_user()
        response = self.client.get(reverse(self.VIEW_NAME, args=[user.share_owner.id]))
        self.assertEqual(
            response.status_code,
            403,
            "A normal user should not be able to create shares.",
        )

    def test_creates_the_right_amount_of_shares(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=2)
        self.assertEqual(2, share_owner.share_ownerships.count())

        self.login_as_member_office_user()
        start_date = datetime.date(year=2022, month=6, day=17)
        num_shares = 5
        self.client.post(
            reverse(self.VIEW_NAME, args=[share_owner.id]),
            {
                "start_date": start_date,
                "num_shares": num_shares,
            },
            follow=True,
        )

        self.assertEqual(7, share_owner.share_ownerships.count())

    def test_create_shares_creates_log_entry(self):
        user = self.login_as_member_office_user()
        self.assertEqual(CreateShareOwnershipsLogEntry.objects.count(), 0)

        start_date = datetime.date(year=2022, month=6, day=17)
        num_shares = 5
        response = self.client.post(
            reverse(self.VIEW_NAME, args=[user.share_owner.id]),
            {
                "start_date": start_date,
                "num_shares": num_shares,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CreateShareOwnershipsLogEntry.objects.count(), 1)
        log_entry = CreateShareOwnershipsLogEntry.objects.first()
        self.assertEqual(log_entry.start_date, start_date)
        self.assertEqual(log_entry.num_shares, num_shares)

    def test_create_shares_sends_an_email_confirmation(self):
        email_address = "test_address@test.net"
        share_owner: ShareOwner = ShareOwnerFactory.create(email=email_address)

        start_date = datetime.date(year=2022, month=6, day=17)
        num_shares = 3
        self.login_as_member_office_user()

        self.assertEqual(len(mail.outbox), 0)
        self.client.post(
            reverse(self.VIEW_NAME, args=[share_owner.id]),
            {
                "start_date": start_date,
                "num_shares": num_shares,
            },
        )

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            ExtraSharesConfirmationEmail, email_address, sent_mail
        )

        self.assertEqual(1, len(sent_mail.attachments))
        self.assertEmailAttachmentIsAPdf(sent_mail.attachments[0])

    def test_creating_shares_creates_an_accounting_recap_entry(self):
        share_owner: ShareOwner = ShareOwnerFactory.create()
        start_date = datetime.date(year=2022, month=6, day=17)
        num_shares = 3
        self.login_as_member_office_user()

        self.assertEqual(0, ExtraSharesForAccountingRecap.objects.count())
        self.client.post(
            reverse(self.VIEW_NAME, args=[share_owner.id]),
            {
                "start_date": start_date,
                "num_shares": num_shares,
            },
        )
        self.assertEqual(1, ExtraSharesForAccountingRecap.objects.count())
        recap_entry = ExtraSharesForAccountingRecap.objects.all()[0]
        self.assertEqual(share_owner, recap_entry.member)
        self.assertEqual(3, recap_entry.number_of_shares)
        self.assertEqual(timezone.now().date(), recap_entry.date)

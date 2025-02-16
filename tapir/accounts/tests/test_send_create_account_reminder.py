import datetime
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command

from tapir.accounts.emails.create_account_reminder_email import (
    CreateAccountReminderEmailBuilder,
)
from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestMixin


class TestCreateAccountReminderMail(TapirFactoryTestBase, TapirEmailTestMixin):
    NOW = datetime.datetime(year=2023, month=8, day=7, hour=10, minute=7)

    def setUp(self) -> None:
        super().setUp()
        patcher = patch("django.utils.timezone.now")
        self.mock_now = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_now.return_value = self.NOW

    def test_sendCreateAccountReminders_sendsEmailOnlyWhenNeeded(self):
        # user that receives reminder
        share_owner = ShareOwner.objects.create(
            first_name="Joe",
            create_account_reminder_email_sent=False,
            is_investing=False,
            email="joe@gmx.de",
        )
        share_owner.save()
        self.save_share_ownership(share_owner, 35)
        # other users that shouldn't receive reminder
        new_share_owner = ShareOwner.objects.create(
            first_name="Dean",
            create_account_reminder_email_sent=False,
            is_investing=False,
            email="dean@gmx.de",
        )
        new_share_owner.save()
        self.save_share_ownership(new_share_owner, 1)
        received_reminder = ShareOwner.objects.create(
            first_name="George",
            create_account_reminder_email_sent=True,
            is_investing=False,
            email="george@gmx.de",
        )
        received_reminder.save()
        self.save_share_ownership(received_reminder, 100)
        investing_user = ShareOwner.objects.create(
            first_name="Jane",
            create_account_reminder_email_sent=False,
            is_investing=True,
            email="jane@gmx.de",
        )
        investing_user.save()
        self.save_share_ownership(investing_user, 100)

        call_command("send_create_account_reminder")

        share_owner.refresh_from_db()
        self.assertTrue(share_owner.create_account_reminder_email_sent)
        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            CreateAccountReminderEmailBuilder,
            share_owner.email,
            sent_mail,
        )
        self.assertIn(share_owner.first_name, sent_mail.body)

    def save_share_ownership(self, share_owner, days_delta):
        share_ownership = ShareOwnership.objects.create(
            share_owner=share_owner,
            start_date=self.NOW - timedelta(days=days_delta),
        )
        share_ownership.save()

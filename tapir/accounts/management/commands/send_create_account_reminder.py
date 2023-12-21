import time
from datetime import timedelta

from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone

from tapir.accounts.emails.create_account_reminder_email import (
    CreateAccountReminderEmail,
)
from tapir.coop.models import ShareOwner


class Command(BaseCommand):
    help = "Sends reminder emails to active members if they haven't created the account 1 month after becoming members"

    def handle(self, *args, **options):
        month_ago = timezone.now() - timedelta(days=31)
        for owners_to_remind in ShareOwner.objects.filter(
            user__isnull=True,
            is_investing=False,
            create_account_reminder_email_sent=False,
            share_ownerships__start_date__lt=month_ago,
        ).all():
            self.send_create_account_reminder_for_user(owners_to_remind)

    @staticmethod
    def send_create_account_reminder_for_user(share_owner: ShareOwner):
        with transaction.atomic():
            mail = CreateAccountReminderEmail(share_owner)
            mail.send_to_share_owner(actor=None, recipient=share_owner)
            share_owner.create_account_reminder_email_sent = True
            share_owner.save()
        time.sleep(0.1)

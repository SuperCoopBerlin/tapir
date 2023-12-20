import time

from django.core.management import BaseCommand
from django.db import transaction

from tapir.accounts.emails.create_account_reminder_email import (
    CreateAccountReminderEmail,
)
from tapir.coop.models import DraftUser


class Command(BaseCommand):
    help = "Sends reminder emails to active members if they haven't created the account 1 month after becoming members"

    def handle(self, *args, **options):
        for active_users_without_account in DraftUser.objects.all():
            self.send_create_account_reminder_for_user(active_users_without_account)

    @staticmethod
    def send_create_account_reminder_for_user(user: DraftUser):
        with transaction.atomic():
            mail = CreateAccountReminderEmail()
            mail.send_to_tapir_user(actor=None, recipient=user)

            # TODO reminder email sent = True
            # TODO save
        time.sleep(0.1)

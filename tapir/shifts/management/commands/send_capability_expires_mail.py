import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.capability_expires_email import CapabilityExpiresEmailBuilder
from tapir.shifts.models import UserCapability


class Command(BaseCommand):
    help = "Sends reminders that a qualification will expire"

    def handle(self, *args, **options):
        for usercapability in UserCapability.objects.all():
            if usercapability.expires_soon(
                min_timedelta=timedelta(weeks=7, days=6),
                max_timedelta=timedelta(weeks=8),
            ):
                self.send_capability_expires_reminder_user(usercapability)

    @staticmethod
    def send_capability_expires_reminder_user(usercapability: UserCapability):

        with transaction.atomic():
            email_builder = CapabilityExpiresEmailBuilder(usercapability=usercapability)
            user = usercapability.shift_user_data.user
            SendMailService.send_to_tapir_user(
                actor=None, recipient=user, email_builder=email_builder
            )

        time.sleep(0.1)

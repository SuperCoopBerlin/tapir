import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template import loader
from django.utils import timezone

from tapir.core.models import FeatureFlag
from tapir.shifts.config import (
    FEATURE_FLAG_REMINDER_MAIL_OLD_PENDING_ATTENDANCES,
    NB_DAYS_BEFORE_REMINDER_OLD_PENDING_ATTENDANCES,
)
from tapir.shifts.models import ShiftAttendance


class Command(BaseCommand):
    help = "Sends a mail to the member office (settings.EMAIL_ADDRESS_MEMBER_OFFICE) if there are shift attendances that are pending since too long"

    def handle(self, *args, **options):
        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_REMINDER_MAIL_OLD_PENDING_ATTENDANCES
        ):
            return

        relevant_attendances = ShiftAttendance.objects.filter(
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
            slot__shift__start_time__lt=timezone.now()
            - datetime.timedelta(days=NB_DAYS_BEFORE_REMINDER_OLD_PENDING_ATTENDANCES),
        ).order_by("slot__shift__start_time")

        if relevant_attendances.count() == 0:
            return

        context = {
            "relevant_attendances": relevant_attendances,
            "site_url": settings.SITE_URL,
            "nb_days_threshold": NB_DAYS_BEFORE_REMINDER_OLD_PENDING_ATTENDANCES,
        }
        body = loader.render_to_string(
            [
                "shifts/email/reminder_old_pending_attendances.body.html",
                "shifts/email/reminder_old_pending_attendances.body.default.html",
            ],
            context,
        )
        subject = loader.render_to_string(
            [
                "shifts/email/reminder_old_pending_attendances.subject.html",
                "shifts/email/reminder_old_pending_attendances.subject.default.html",
            ],
            context,
        )

        email = EmailMultiAlternatives(
            subject="".join(subject.splitlines()),
            body=body,
            to=[settings.EMAIL_ADDRESS_MEMBER_OFFICE],
            from_email=settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        )
        email.content_subtype = "html"
        email.send()

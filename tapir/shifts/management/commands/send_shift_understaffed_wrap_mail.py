import datetime
import time

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from tapir.core.services.optional_mails_for_user_service import (
    OptionalMailsForUserService,
)
from tapir.core.services.send_mail_service import SendMailService
from django.utils import timezone

from tapir.shifts.emails.shift_understaffed_wrap_mail import (
    ShiftUnderstaffedWrapEmailBuilder,
)
from tapir.shifts.models import Shift


class Command(BaseCommand):
    help = "Sends emails to interested members that a certain shift is understaffed"

    def handle(self, *args, **options):
        end_of_next_day = timezone.now().today().replace(
            hour=23, minute=59, second=59
        ) + datetime.timedelta(days=1)
        # all understaffed shifts from now on and tommorrow
        shifts = Shift.objects.filter(
            start_time__gte=timezone.now(),
            start_time__lte=end_of_next_day,
        )
        shift_understaffed_ids_in = [
            shift.id
            for shift in shifts
            if (
                shift.get_valid_attendances().count()
                < shift.get_num_required_attendances()
            )
        ]
        self.send_shift_understaffed_mail(
            shifts.filter(id__in=shift_understaffed_ids_in)
        )

    @staticmethod
    def send_shift_understaffed_mail(shifts: QuerySet[Shift]):
        for user in OptionalMailsForUserService.get_users_want_to_receive_optional_mail(
            ShiftUnderstaffedWrapEmailBuilder
        ):
            email_builder = ShiftUnderstaffedWrapEmailBuilder(shifts=shifts)
            SendMailService.send_to_tapir_user(
                actor=None,
                recipient=user,
                email_builder=email_builder,
            )

            time.sleep(0.1)

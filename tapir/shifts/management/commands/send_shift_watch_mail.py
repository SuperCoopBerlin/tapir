import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.models import ShiftWatch, StaffingStatus, Shift, ShiftStaffingStatus
from tapir.shifts.utils import get_current_shiftwatch


def calculate_status(shift: Shift):

    if shift.get_valid_attendances().count() < shift.get_num_required_attendances():
        return StaffingStatus.UNDERSTAFFED
    elif shift.get_valid_attendances().count():
        return StaffingStatus.ALMOST_FULL
    return None


class Command(BaseCommand):
    help = "Sent to a member when there is a relevant change in shift staffing and the member wants to know about it."

    def handle(self, *args, **options):
        for shift_watch_data in get_current_shiftwatch():
            current_status, created = ShiftStaffingStatus.objects.get_or_create(
                shift=shift_watch_data.shift
            )
            if (
                shift_watch_data.last_reason_for_notification
                != current_status.staffing_status
            ) & (current_status.staffing_status != StaffingStatus.__empty__):
                self.send_shift_watch_mail(
                    shift_watch_data, reason=current_status.staffing_status
                )
                shift_watch_data.last_reason_for_notification = (
                    current_status.staffing_status
                )

    @staticmethod
    def send_shift_watch_mail(shift_watches: ShiftWatch, reason: str):
        for shift_watch in shift_watches.objects.select_related("user", "shift"):
            with transaction.atomic():
                email_builder = ShiftWatchEmailBuilder(
                    shift=shift_watch.shift,
                    reason=f"{reason}: {shift_watch.shift.get_display_name()}",
                )
                SendMailService.send_to_tapir_user(
                    actor=None,
                    recipient=shift_watch.user,
                    email_builder=email_builder,
                )
                shift_watch.notification_sent = True
                shift_watch.save()
            time.sleep(0.1)

import time

from django.core.management.base import BaseCommand

from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_service import FrozenStatusService


class Command(BaseCommand):
    help = (
        "Check all members and freeze them or unfreeze them if required."
        "Also sends emails depending on those changes."
    )

    def handle(self, *args, **options):
        for shift_user_data in ShiftUserData.objects.all():
            if FrozenStatusService.should_freeze_member(shift_user_data):
                FrozenStatusService.freeze_member_and_send_email(
                    shift_user_data, actor=None
                )
                time.sleep(0.1)
                continue

            if FrozenStatusService.should_send_freeze_warning(shift_user_data):
                FrozenStatusService.send_freeze_warning_email(shift_user_data)
                time.sleep(0.1)
                continue

            if FrozenStatusService.should_unfreeze_member(shift_user_data):
                FrozenStatusService.send_unfreeze_notification_email(shift_user_data)
                time.sleep(0.1)

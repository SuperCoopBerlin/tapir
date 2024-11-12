import time

from django.core.management.base import BaseCommand

from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_management_service import (
    FrozenStatusManagementService,
)


class Command(BaseCommand):
    help = (
        "Check all members and freeze them or unfreeze them if required."
        "Also sends emails depending on those changes."
    )

    def handle(self, *args, **options):
        for shift_user_data in ShiftUserData.objects.all():
            if FrozenStatusManagementService.should_freeze_member(shift_user_data):
                FrozenStatusManagementService.freeze_member_and_send_email(
                    shift_user_data, actor=None
                )
                time.sleep(0.1)
                continue

            if FrozenStatusManagementService.should_send_freeze_warning(
                shift_user_data
            ):
                FrozenStatusManagementService.send_freeze_warning_email(shift_user_data)
                time.sleep(0.1)
                continue

            if FrozenStatusManagementService.should_unfreeze_member(shift_user_data):
                FrozenStatusManagementService.unfreeze_and_send_notification_email(
                    shift_user_data
                )
                time.sleep(0.1)

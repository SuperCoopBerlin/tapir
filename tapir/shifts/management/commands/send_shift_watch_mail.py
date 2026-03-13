import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.emails.shift_watch_mail import (
    ShiftWatchEmailBuilder,
)
from tapir.shifts.models import (
    ShiftWatch,
    StaffingStatusChoices,
    ShiftUserCapability,
    ShiftSlot,
    SHIFT_USER_CAPABILITY_CHOICES,
)
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator


def get_capability_status_changes(
    this_valid_slot_ids: list[int],
    last_valid_slot_ids: list[int],
    watched_capabilities: list[str],
) -> list[SHIFT_USER_CAPABILITY_CHOICES]:
    if not watched_capabilities:
        return []

    notifications = []

    current_slots = ShiftSlot.objects.filter(id__in=this_valid_slot_ids).values_list(
        "id", "required_capabilities"
    )

    last_slots = (
        ShiftSlot.objects.filter(id__in=last_valid_slot_ids).values_list(
            "id", "required_capabilities"
        )
        if last_valid_slot_ids
        else []
    )

    current_capabilities_set = set()
    for slot_id, capabilities in current_slots:
        current_capabilities_set.update(capabilities)

    last_capabilities_set = set()
    for slot_id, capabilities in last_slots:
        last_capabilities_set.update(capabilities)

    for capability in watched_capabilities:
        has_now = capability in current_capabilities_set
        had_before = capability in last_capabilities_set

        if has_now and not had_before:
            notifications.append(StaffingStatusChoices.ATTENDANCE_PLUS)
        elif not has_now and had_before:
            notifications.append(StaffingStatusChoices.ATTENDANCE_PLUS)
    return notifications


class Command(BaseCommand):
    help = "Sent to a member when there is a relevant change in shift staffing and the member wants to know about it."

    def handle(self, *args, **options):
        for shift_watch_data in ShiftWatch.objects.filter(
            shift__end_time__gte=timezone.now()  # end_time not start_time because flexible-shifts can be running the whole day
        ).select_related("user", "shift"):
            self.send_shift_watch_mail_per_user_and_shift(shift_watch_data)

    def send_shift_watch_mail_per_user_and_shift(self, shift_watch_data: ShiftWatch):
        notification_reasons: list[StaffingStatusChoices] = []

        this_valid_slot_ids = ShiftWatchCreator.get_valid_slot_ids(
            shift_watch_data.shift
        )

        valid_attendances_count = len(this_valid_slot_ids)
        required_attendances_count = (
            shift_watch_data.shift.get_num_required_attendances()
        )
        number_of_available_slots = shift_watch_data.shift.slots.count()

        # Determine staffing status
        current_status = ShiftWatchCreator.get_staffing_status_if_changed(
            number_of_available_slots=number_of_available_slots,
            valid_attendances=valid_attendances_count,
            required_attendances=required_attendances_count,
            last_status=shift_watch_data.last_staffing_status,
        )
        if current_status:
            notification_reasons.append(current_status)
            shift_watch_data.last_staffing_status = current_status

        # Check watched capabilities
        if shift_watch_data.watched_capabilities:

            capability_notifications = get_capability_status_changes(
                this_valid_slot_ids=this_valid_slot_ids,
                last_valid_slot_ids=shift_watch_data.last_valid_slot_ids,
                watched_capabilities=shift_watch_data.watched_capabilities,
            )

            # Füge Benachrichtigungen hinzu
            for status_enum in capability_notifications:
                notification_reasons.append(status_enum)

        # General attendance change notifications
        if not notification_reasons:
            # If no other status like "Understaffed" or "teamleader registered" appeared, inform user about general change
            if valid_attendances_count > len(shift_watch_data.last_valid_slot_ids):
                notification_reasons.append(StaffingStatusChoices.ATTENDANCE_PLUS)
            elif valid_attendances_count < len(shift_watch_data.last_valid_slot_ids):
                notification_reasons.append(StaffingStatusChoices.ATTENDANCE_MINUS)

        # Send notifications
        for reason in notification_reasons:
            if reason.value in shift_watch_data.staffing_status:
                self.send_shift_watch_mail(
                    shift_watch=shift_watch_data, staffing_status=reason
                )

        shift_watch_data.last_valid_slot_ids = this_valid_slot_ids
        shift_watch_data.save()

    @staticmethod
    def send_shift_watch_mail(
        shift_watch: ShiftWatch, staffing_status: StaffingStatusChoices
    ):
        email_builder = ShiftWatchEmailBuilder(
            shift_watch=shift_watch,
            staffing_status=staffing_status,
        )
        SendMailService.send_to_tapir_user(
            actor=None,
            recipient=shift_watch.user,
            email_builder=email_builder,
        )
        time.sleep(0.1)

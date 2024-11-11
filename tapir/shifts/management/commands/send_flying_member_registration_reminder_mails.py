import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from tapir.log.models import EmailLogEntry
from tapir.shifts.emails.flying_member_registration_reminder_email import (
    FlyingMemberRegistrationReminderEmail,
)
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    ShiftCycleEntry,
    ShiftAttendance,
)
from tapir.shifts.services.shift_cycle_service import ShiftCycleService
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService


class Command(BaseCommand):
    help = "Send FlyingMemberRegistrationReminderEmail if necessary."

    def handle(self, *args, **options):
        start_date = ShiftCycleService.get_start_date_of_current_cycle()
        end_date = start_date + datetime.timedelta(
            days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
        )
        if timezone.now().date() > end_date - datetime.timedelta(days=7):
            # Don't send mails if the cycle is about to end
            return

        flying_members = ShiftUserData.objects.filter(
            attendance_mode=ShiftAttendanceMode.FLYING
        )
        for shift_user_data in flying_members:
            if not self.should_member_receive_reminder_mail(
                shift_user_data, start_date
            ):
                continue
            FlyingMemberRegistrationReminderEmail().send_to_tapir_user(
                actor=None, recipient=shift_user_data.user
            )

    @classmethod
    def should_member_receive_reminder_mail(cls, shift_user_data, start_date):
        if not ShiftExpectationService.is_member_expected_to_do_shifts(shift_user_data):
            return False
        if cls.has_user_received_reminder_this_cycle(shift_user_data, start_date):
            return False
        if cls.is_member_registered_to_a_shift_this_cycle(shift_user_data, start_date):
            return False
        return True

    @staticmethod
    def has_user_received_reminder_this_cycle(
        shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        cycle_end_date = cycle_start_date + datetime.timedelta(
            days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
        )
        return EmailLogEntry.objects.filter(
            email_id=FlyingMemberRegistrationReminderEmail.get_unique_id(),
            user=shift_user_data.user,
            created_date__gte=cycle_start_date,
            created_date__lte=cycle_end_date,
        ).exists()

    @staticmethod
    def is_member_registered_to_a_shift_this_cycle(
        shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        return ShiftAttendance.objects.filter(
            user=shift_user_data.user,
            slot__shift__start_time__date__gte=cycle_start_date,
            slot__shift__start_time__date__lt=cycle_start_date
            + datetime.timedelta(days=ShiftCycleEntry.SHIFT_CYCLE_DURATION),
        ).exists()

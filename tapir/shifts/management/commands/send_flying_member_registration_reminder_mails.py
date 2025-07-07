import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from tapir.core.models import FeatureFlag
from tapir.core.services.send_mail_service import SendMailService
from tapir.log.models import EmailLogEntry
from tapir.shifts.config import FEATURE_FLAG_FLYING_MEMBERS_REGISTRATION_REMINDER
from tapir.shifts.emails.flying_member_registration_reminder_email import (
    FlyingMemberRegistrationReminderEmailBuilder,
)
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    ShiftCycleEntry,
    ShiftAttendance,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_cycle_service import ShiftCycleService
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService


class Command(BaseCommand):
    help = "Send FlyingMemberRegistrationReminderEmail if necessary."

    def handle(self, *args, **options):
        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_FLYING_MEMBERS_REGISTRATION_REMINDER
        ):
            return

        start_date = ShiftCycleService.get_start_date_of_current_cycle()
        end_date = start_date + datetime.timedelta(
            days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
        )
        if timezone.now().date() > end_date - datetime.timedelta(days=7):
            # Don't send mails if the cycle is about to end
            return

        reference_time = timezone.now()
        shift_user_datas = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_time
        )
        shift_user_datas.select_related("user")

        for shift_user_data in shift_user_datas:
            if (
                ShiftAttendanceModeService.get_attendance_mode(
                    shift_user_data, reference_time
                )
                != ShiftAttendanceMode.FLYING
            ):
                continue

            if not self.should_member_receive_reminder_mail(
                shift_user_data, start_date, reference_time
            ):
                continue

            email_builder = FlyingMemberRegistrationReminderEmailBuilder()
            SendMailService.send_to_tapir_user(
                actor=None, recipient=shift_user_data.user, email_builder=email_builder
            )

    @classmethod
    def should_member_receive_reminder_mail(
        cls, shift_user_data, start_date, reference_time
    ):
        if not ShiftExpectationService.is_member_expected_to_do_shifts(
            shift_user_data, reference_time
        ):
            return False
        if cls.has_user_received_reminder_this_cycle(shift_user_data, start_date):
            return False
        if cls.is_member_registered_to_a_shift_this_cycle(shift_user_data, start_date):
            return False
        if start_date + datetime.timedelta(days=7) > timezone.now().date():
            return False
        if cls.is_users_first_cycle(shift_user_data, start_date):
            return False

        return True

    @staticmethod
    def is_users_first_cycle(
        shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        return (
            ShiftCycleService.get_start_date_of_current_cycle(
                today=shift_user_data.user.date_joined.date()
            )
            + datetime.timedelta(days=ShiftCycleEntry.SHIFT_CYCLE_DURATION)
            == cycle_start_date
        )

    @staticmethod
    def has_user_received_reminder_this_cycle(
        shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        cycle_end_date = cycle_start_date + datetime.timedelta(
            days=ShiftCycleEntry.SHIFT_CYCLE_DURATION
        )
        return EmailLogEntry.objects.filter(
            email_id=FlyingMemberRegistrationReminderEmailBuilder.get_unique_id(),
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
            state__in=ShiftAttendance.VALID_STATES,
        ).exists()

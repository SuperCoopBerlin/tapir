import datetime

from django.db import transaction
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.log.models import EmailLogEntry
from tapir.log.util import freeze_for_log
from tapir.shifts.config import FREEZE_THRESHOLD, FREEZE_AFTER_DAYS
from tapir.shifts.emails.freeze_warning_email import FreezeWarningEmail
from tapir.shifts.emails.member_frozen_email import MemberFrozenEmail
from tapir.shifts.emails.unfreeze_notification_email import UnfreezeNotificationEmail
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceTemplate,
    ShiftAccountEntry,
    ShiftAttendance,
)


class FrozenStatusService:
    @classmethod
    def should_freeze_member(cls, shift_user_data: ShiftUserData) -> bool:
        if shift_user_data.attendance_mode is ShiftAttendanceMode.FROZEN:
            return False

        if not cls._is_member_below_threshold_since_long_enough(shift_user_data):
            return False

        if cls._is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
            shift_user_data
        ):
            return False

        return True

    @classmethod
    def _is_member_below_threshold_since_long_enough(
        cls, shift_user_data: ShiftUserData
    ) -> bool:
        balance = shift_user_data.get_account_balance()
        if balance > FREEZE_THRESHOLD:
            return False

        entries = ShiftAccountEntry.objects.filter(user=shift_user_data.user).order_by(
            "-date"
        )
        for entry in entries:
            if (timezone.now().date() - entry.date.date()).days > FREEZE_AFTER_DAYS:
                return True
            balance -= entry.value
            if balance > FREEZE_THRESHOLD:
                return False

    @classmethod
    def _is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
        cls, shift_user_data: ShiftUserData
    ) -> bool:
        upcoming_shifts = ShiftAttendance.objects.filter(
            user=shift_user_data.user,
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
            slot__shift__start_time__gt=timezone.now(),
            slot__shift__start_time__lt=timezone.now() + datetime.timedelta(weeks=8),
        )
        return upcoming_shifts.count() >= -shift_user_data.get_account_balance()

    @classmethod
    def freeze_member_and_send_email(
        cls, shift_user_data: ShiftUserData, actor: TapirUser | None
    ):
        with transaction.atomic():
            cls._update_attendance_mode_and_create_log_entry(
                shift_user_data, actor, ShiftAttendanceMode.FROZEN
            )
            cls._cancel_future_attendances_templates(shift_user_data)
            ShiftAttendanceTemplate.objects.filter(user=shift_user_data.user).delete()
        email = MemberFrozenEmail()
        email.send_to_tapir_user(actor=actor, recipient=shift_user_data.user)

    @staticmethod
    def _update_attendance_mode_and_create_log_entry(
        shift_user_data: ShiftUserData, actor: TapirUser | None, attendance_mode: str
    ):
        old_data = freeze_for_log(shift_user_data)
        shift_user_data.attendance_mode = attendance_mode
        new_data = freeze_for_log(shift_user_data)
        shift_user_data.save()
        if old_data != new_data:
            UpdateShiftUserDataLogEntry().populate(
                old_frozen=old_data,
                new_frozen=new_data,
                tapir_user=shift_user_data.user,
                actor=actor,
            ).save()

    @staticmethod
    def _cancel_future_attendances_templates(shift_user_data: ShiftUserData):
        for attendance_template in ShiftAttendanceTemplate.objects.filter(
            user=shift_user_data.user
        ):
            attendance_template.cancel_attendances(timezone.now())
            attendance_template.delete()

    @classmethod
    def should_send_freeze_warning(cls, shift_user_data: ShiftUserData):
        if shift_user_data.get_account_balance() > FREEZE_THRESHOLD:
            return False

        last_warning = (
            EmailLogEntry.objects.filter(
                email_id=FreezeWarningEmail.get_unique_id(),
                user=shift_user_data.user,
            )
            .order_by("-created_date")
            .first()
        )

        if last_warning is None:
            return True

        return (
            timezone.now().date() - last_warning.created_date.date()
        ).days > FREEZE_AFTER_DAYS

    @staticmethod
    def send_freeze_warning_email(shift_user_data: ShiftUserData):
        email = FreezeWarningEmail()
        email.send_to_tapir_user(actor=None, recipient=shift_user_data.user)

    @classmethod
    def should_unfreeze_member(cls, shift_user_data: ShiftUserData):
        if shift_user_data.attendance_mode != ShiftAttendanceMode.FROZEN:
            return False

        if shift_user_data.get_account_balance() >= 0:
            return True

        return cls._is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
            shift_user_data
        )

    @classmethod
    def unfreeze_and_send_notification_email(
        cls, shift_user_data: ShiftUserData, actor: None | TapirUser = None
    ):

        cls._update_attendance_mode_and_create_log_entry(
            shift_user_data=shift_user_data,
            actor=actor,
            attendance_mode=cls._get_last_attendance_mode_before_frozen(
                shift_user_data
            ),
        )
        email = UnfreezeNotificationEmail()
        email.send_to_tapir_user(actor=actor, recipient=shift_user_data.user)

    @staticmethod
    def _get_last_attendance_mode_before_frozen(shift_user_data: ShiftUserData):
        last_freeze_log_entry = (
            UpdateShiftUserDataLogEntry.objects.filter(
                new_values__attendance_mode=ShiftAttendanceMode.FROZEN,
                user=shift_user_data.user,
            )
            .order_by("-created_date")
            .first()
        )

        return (
            last_freeze_log_entry.old_values["attendance_mode"]
            if last_freeze_log_entry
            else ShiftAttendanceMode.FLYING
        )

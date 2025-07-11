import datetime

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.core.services.send_mail_service import SendMailService
from tapir.log.models import EmailLogEntry
from tapir.log.util import freeze_for_log
from tapir.shifts.config import (
    FREEZE_THRESHOLD,
    FREEZE_AFTER_DAYS,
    NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS,
)
from tapir.shifts.emails.freeze_warning_email import FreezeWarningEmailBuilder
from tapir.shifts.emails.member_frozen_email import MemberFrozenEmailBuilder
from tapir.shifts.emails.unfreeze_notification_email import (
    UnfreezeNotificationEmailBuilder,
)
from tapir.shifts.models import (
    ShiftUserData,
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceTemplate,
    ShiftAccountEntry,
    ShiftAttendance,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService


class FrozenStatusManagementService:
    @classmethod
    def should_freeze_member(cls, shift_user_data: ShiftUserData) -> bool:
        if shift_user_data.is_frozen:
            return False

        if not ShiftExpectationService.is_member_expected_to_do_shifts(
            shift_user_data, timezone.now()
        ):
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
            slot__shift__start_time__lt=timezone.now()
            + datetime.timedelta(weeks=NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS),
        )

        return (
            upcoming_shifts.count() + shift_user_data.get_account_balance()
            > FREEZE_THRESHOLD
        )

    @classmethod
    def freeze_member_and_send_email(
        cls, shift_user_data: ShiftUserData, actor: TapirUser | User | None
    ):
        with transaction.atomic():
            cls._update_frozen_status_and_create_log_entry(shift_user_data, actor, True)
            cls._cancel_future_attendances_templates(shift_user_data)
            attendance_templates_to_delete = ShiftAttendanceTemplate.objects.filter(
                user=shift_user_data.user
            )
            for attendance_template in attendance_templates_to_delete:
                DeleteShiftAttendanceTemplateLogEntry().populate(
                    actor=actor,
                    tapir_user=shift_user_data.user,
                    shift_attendance_template=attendance_template,
                    comment="Unregistered because frozen",
                ).save()
            attendance_templates_to_delete.delete()
        email_builder = MemberFrozenEmailBuilder()
        SendMailService.send_to_tapir_user(
            actor=actor, recipient=shift_user_data.user, email_builder=email_builder
        )

    @staticmethod
    def _update_frozen_status_and_create_log_entry(
        shift_user_data: ShiftUserData, actor: TapirUser | User | None, is_frozen: bool
    ):
        old_data = freeze_for_log(shift_user_data)
        shift_user_data.is_frozen = is_frozen
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

    @classmethod
    def should_send_freeze_warning(cls, shift_user_data: ShiftUserData):
        if shift_user_data.get_account_balance() > FREEZE_THRESHOLD:
            return False

        if not ShiftExpectationService.is_member_expected_to_do_shifts(
            shift_user_data, timezone.now()
        ):
            return False

        last_warning = (
            EmailLogEntry.objects.filter(
                email_id=FreezeWarningEmailBuilder.get_unique_id(),
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
        email_builder = FreezeWarningEmailBuilder(shift_user_data)
        SendMailService.send_to_tapir_user(
            actor=None, recipient=shift_user_data.user, email_builder=email_builder
        )

    @classmethod
    def should_unfreeze_member(cls, shift_user_data: ShiftUserData):
        if not shift_user_data.is_frozen:
            return False

        if not shift_user_data.user.share_owner.is_active():
            return False

        if shift_user_data.get_account_balance() > FREEZE_THRESHOLD:
            return True

        return cls._is_member_registered_to_enough_shifts_to_compensate_for_negative_shift_account(
            shift_user_data
        )

    @classmethod
    def unfreeze_and_send_notification_email(
        cls, shift_user_data: ShiftUserData, actor: None | TapirUser = None
    ):
        cls._update_frozen_status_and_create_log_entry(
            shift_user_data=shift_user_data,
            actor=actor,
            is_frozen=False,
        )
        email_builder = UnfreezeNotificationEmailBuilder()
        SendMailService.send_to_tapir_user(
            actor=actor, recipient=shift_user_data.user, email_builder=email_builder
        )

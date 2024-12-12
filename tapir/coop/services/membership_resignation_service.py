import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q

from tapir.accounts.models import TapirUser
from tapir.coop.models import MembershipResignation, ShareOwnership, MembershipPause
from tapir.shifts.models import (
    ShiftAttendanceTemplate,
    ShiftAttendance,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.utils.shortcuts import get_timezone_aware_datetime


class MembershipResignationService:
    @staticmethod
    @transaction.atomic
    def update_shifts_and_shares_and_pay_out_day(
        resignation: MembershipResignation, actor: TapirUser | User
    ):
        shares = ShareOwnership.objects.filter(share_owner=resignation.share_owner)
        end_date_null_or_after_cancellation_filter = Q(end_date__isnull=True) | Q(
            end_date__gte=resignation.cancellation_date
        )
        shares = shares.filter(end_date_null_or_after_cancellation_filter)

        match resignation.resignation_type:
            case MembershipResignation.ResignationType.BUY_BACK:
                new_end_date = resignation.cancellation_date + relativedelta(
                    years=+3, day=31, month=12
                )
                resignation.pay_out_day = new_end_date
                resignation.save()
                end_date_null_or_after_pay_out_day_filter = Q(
                    end_date__isnull=True
                ) | Q(end_date__gte=resignation.pay_out_day)
                shares = shares.filter(end_date_null_or_after_pay_out_day_filter)
                shares.update(end_date=new_end_date)
                return
            case MembershipResignation.ResignationType.GIFT_TO_COOP:
                resignation.pay_out_day = resignation.cancellation_date
                resignation.save()
                shares.update(end_date=resignation.cancellation_date)
            case MembershipResignation.ResignationType.TRANSFER:
                shares.update(end_date=resignation.cancellation_date)
                resignation.pay_out_day = resignation.cancellation_date
                resignation.save()
                shares_to_create = [
                    ShareOwnership(
                        share_owner=resignation.transferring_shares_to,
                        start_date=resignation.cancellation_date
                        + datetime.timedelta(days=1),
                        transferred_from=share,
                    )
                    for share in shares
                ]
                ShareOwnership.objects.bulk_create(shares_to_create)
            case _:
                raise ValueError(
                    f"Unknown resignation type: {resignation.resignation_type}"
                )

        tapir_user: TapirUser = getattr(resignation.share_owner, "user", None)
        if not tapir_user:
            return

        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation, actor=actor
        )

    @staticmethod
    def update_shifts(
        tapir_user: TapirUser,
        resignation: MembershipResignation,
        actor: TapirUser | User,
    ):
        start_date = get_timezone_aware_datetime(
            resignation.cancellation_date, datetime.time()
        )

        for attendance_template in ShiftAttendanceTemplate.objects.filter(
            user=tapir_user,
        ):
            attendance_template.cancel_attendances(starting_from=start_date)
            DeleteShiftAttendanceTemplateLogEntry().populate(
                actor=actor,
                tapir_user=tapir_user,
                shift_attendance_template=attendance_template,
                comment="Unregistered because of membership resignation",
            ).save()
            attendance_template.delete()

        attendances = ShiftAttendance.objects.filter(
            user=tapir_user,
            slot__shift__start_time__gte=start_date,
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
        )
        attendances.update(state=ShiftAttendance.State.CANCELLED)

    @classmethod
    def on_resignation_deleted(cls, resignation: MembershipResignation):
        cls.delete_transferred_share_ownerships(resignation)
        cls.delete_end_dates(resignation)

    @staticmethod
    def delete_end_dates(resignation: MembershipResignation):
        resignation.share_owner.share_ownerships.filter(
            end_date=resignation.cancellation_date
        ).update(end_date=None)

    @classmethod
    def delete_transferred_share_ownerships(cls, resignation: MembershipResignation):
        if (
            not resignation.resignation_type
            == MembershipResignation.ResignationType.TRANSFER
        ):
            return
        ended_ownerships = resignation.share_owner.share_ownerships.filter(
            end_date=resignation.cancellation_date
        )
        started_ownerships = ShareOwnership.objects.filter(
            share_owner=resignation.transferring_shares_to,
            start_date=resignation.cancellation_date + datetime.timedelta(days=1),
            transferred_from__in=ended_ownerships,
        )
        for started_ownership in started_ownerships:
            cls.delete_share_ownership_and_all_transfers(started_ownership)

    @classmethod
    def delete_share_ownership_and_all_transfers(cls, share_ownership: ShareOwnership):
        transferred = ShareOwnership.objects.filter(
            transferred_from=share_ownership
        ).first()
        if transferred:
            cls.delete_share_ownership_and_all_transfers(transferred)
        share_ownership.delete()

    @staticmethod
    def update_membership_pauses(resignation: MembershipResignation):
        for pause in MembershipPause.objects.filter(
            share_owner=resignation.share_owner
        ):
            if pause.start_date > resignation.pay_out_day:
                pause.delete()
                return

            if pause.end_date is not None and pause.end_date <= resignation.pay_out_day:
                return

            pause.end_date = resignation.pay_out_day
            pause.save()

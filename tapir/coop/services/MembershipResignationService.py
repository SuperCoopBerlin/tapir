import datetime

from django.db import transaction
from tapir.accounts.models import TapirUser
from tapir.coop.models import MembershipResignation, ShareOwnership
from tapir.shifts.models import (
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftAccountEntry,
)
from tapir.shifts.services.frozen_status_service import FrozenStatusService
from tapir.shifts.models import ShiftUserData, ShiftAttendanceMode

from tapir.utils.shortcuts import get_timezone_aware_datetime


class MembershipResignationService:
    @staticmethod
    @transaction.atomic
    def update_shifts_and_shares(self, resignation: MembershipResignation):
        tapir_user: TapirUser = getattr(resignation.share_owner, "user", None)
        if not tapir_user:
            print("Couldn't find an existing Tapir user.")
            return

        MembershipResignationService.update_shifts(
            self, tapir_user=tapir_user, resignation=resignation
        )

        shares = ShareOwnership.objects.filter(share_owner=resignation.share_owner)
        if not MembershipResignationService.is_resignation_happening_right_away(
            self, resignation=resignation
        ):
            new_end_date = resignation.cancellation_date.replace(day=31, month=12)
            new_end_date = new_end_date.replace(year=new_end_date.year + 3)
            shares.update(end_date=new_end_date)
            return
        MembershipResignationService.resignation_happens_right_away(
            self, shares=shares, resignation=resignation
        )

    @staticmethod
    def update_shifts(self, tapir_user: TapirUser, resignation: MembershipResignation):
        for attendance_template in ShiftAttendanceTemplate.objects.filter(
            user=tapir_user
        ):
            start_date = get_timezone_aware_datetime(
                resignation.cancellation_date, datetime.time()
            )
            attendance_template.cancel_attendances(start_date)
            attendance_template.delete()

            attendances = ShiftAttendance.objects.filter(
                user=tapir_user,
                slot__shift__start_time__gte=start_date,
                state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
            )
            attendances.update(state=ShiftAttendance.State.CANCELLED)

    @staticmethod
    def is_resignation_happening_right_away(self, resignation: MembershipResignation):
        if (
            resignation.willing_to_gift_shares_to_coop
            or resignation.transfering_shares_to is not None
        ):
            return True
        return False

    @staticmethod
    def resignation_happens_right_away(
        self, shares: list[ShareOwnership], resignation: MembershipResignation
    ):
        if resignation.transfering_shares_to is not None:
            for share in shares:
                ShareOwnership.objects.create(
                    share_owner=resignation.transfering_shares_to,
                    amount_paid=share.amount_paid,
                    start_date=resignation.cancellation_date,
                )
                share.delete()
        elif resignation.willing_to_gift_shares_to_coop:
            shares.update(end_date=datetime.datetime.now())

    @staticmethod
    @transaction.atomic
    def delete_end_dates(member: MembershipResignation):
        ShareOwnership.objects.filter(share_owner=member.share_owner).update(
            end_date=None
        )

import datetime

from tapir.accounts.models import TapirUser
from tapir.coop.models import ResignedMembership, ShareOwnership
from tapir.coop.forms import MembershipCancelForm
from tapir.shifts.models import (
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftAccountEntry,
)
from tapir.shifts.services.frozen_status_service import FrozenStatusService
from tapir.shifts.models import ShiftUserData, ShiftAttendanceMode

from tapir.utils.shortcuts import get_timezone_aware_datetime


class ResignMemberService:
    @staticmethod
    def update_shifts_and_shares(
        form: MembershipCancelForm, member: ResignedMembership
    ):
        tapir_user: TapirUser = getattr(member.share_owner, "user", None)
        if not tapir_user:
            print("Couldn't find an existing Tapir user.")
            return
        shares = ShareOwnership.objects.filter(share_owner=member.share_owner)
        if (
            member.willing_to_gift_shares_to_coop
            or member.transfering_shares_to is not None
        ):
            for share in shares:
                if share.is_fully_paid:
                    if member.transfering_shares_to is not None:
                        ShareOwnership.objects.create(
                            share_owner=member.transfering_shares_to,
                            amount_paid=share.amount_paid,
                            start_date=member.cancellation_date,
                        )
                        share.delete()
                    else:
                        share.is_active = False
                else:
                    raise ValueError(
                        "Shareowner didn't fully paid all shares, so it cannot be tranfered to someone else."
                    )
                    break

            for attendance_template in ShiftAttendanceTemplate.objects.filter(
                user=tapir_user
            ):
                start_date = get_timezone_aware_datetime(
                    member.cancellation_date, datetime.time()
                )
                attendance_template.cancel_attendances(start_date)
                attendance_template.delete()

                attendances = ShiftAttendance.objects.filter(
                    user=tapir_user,
                    slot__shift__start_time__gte=start_date,
                    state=ShiftAttendance.State.PENDING,
                )

                for attendance in attendances:
                    attendance.state = ShiftAttendance.State.CANCELLED
                    attendance.save()

                for shift_account_entry in ShiftAccountEntry.objects.filter(
                    user=tapir_user
                ):
                    shift_account_entry.delete()

                for shift_user_data in ShiftUserData.objects.filter(user=tapir_user):
                    shift_user_data.attendance_mode = (ShiftAttendanceMode.FROZEN,)

            shares.update(end_date=datetime.datetime.now())
        else:
            new_end_date = member.cancellation_date.replace(month=12).replace(day=31)
            new_end_date = new_end_date.replace(year=new_end_date.year + 3)
            shares.update(end_date=new_end_date)

    def delete_end_dates(member: ResignedMembership):
        ShareOwnership.objects.filter(share_owner=member.share_owner).update(
            end_date=None
        )

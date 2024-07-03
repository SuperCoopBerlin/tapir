import datetime

from tapir.accounts.models import TapirUser
from tapir.coop.models import ResignedMembership, ShareOwnership
from tapir.shifts.models import ShiftAttendanceTemplate, ShiftAttendance
from tapir.utils.shortcuts import get_timezone_aware_datetime


class ResignMemberService:
    @staticmethod
    def update_shifts_and_shares(member: ResignedMembership):
        tapir_user: TapirUser = getattr(member.share_owner, "user", None)
        if not tapir_user:
            print("Couldn't find an existing Tapir user.")
            return

        new_end_date = member.cancellation_date
        new_end_date = new_end_date.replace(month=12)
        new_end_date = new_end_date.replace(day=31)
        new_end_date = new_end_date.replace(year=new_end_date.year + 3)
        ShareOwnership.objects.filter(share_owner=member.share_owner).update(
            end_date=new_end_date
        )

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

    def delete_end_dates(member: ResignedMembership):
        ShareOwnership.objects.filter(share_owner=member.share_owner).update(
            end_date=None
        )

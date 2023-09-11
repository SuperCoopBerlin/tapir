import datetime

from django.utils import timezone

from tapir.shifts.models import ShiftUserData, ShiftAttendanceMode


class ShiftExpectationService:
    @staticmethod
    def is_member_expected_to_do_shifts(
        shift_user_data: ShiftUserData, date: datetime.date | None = None
    ) -> bool:
        if date is None:
            date = timezone.now().date()

        if (
            not hasattr(shift_user_data.user, "share_owner")
            or shift_user_data.user.share_owner is None
        ):
            return False

        if shift_user_data.attendance_mode == ShiftAttendanceMode.FROZEN:
            return False

        if shift_user_data.user.date_joined.date() > date:
            return False

        if not shift_user_data.user.share_owner.is_active():
            return False

        if shift_user_data.is_currently_exempted_from_shifts(date):
            return False

        return True

    @classmethod
    def get_credit_requirement_for_cycle(
        cls, shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        if not cls.is_member_expected_to_do_shifts(shift_user_data, cycle_start_date):
            return 0
        return 1

import datetime

from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.models import UpdateShiftUserDataLogEntry, ShiftAttendanceMode
from tapir.statistics.views.fancy_graph.base_view import DatapointView
from tapir.statistics.views.fancy_graph.number_of_frozen_members_view import (
    NumberOfFrozenMembersAtDateView,
)


class NumberOfLongTermFrozenMembersAtDateView(DatapointView):
    permission_required = PERMISSION_COOP_MANAGE

    def get_datapoint(self, reference_time: datetime.datetime):
        share_owners = NumberOfFrozenMembersAtDateView.get_members_frozen_at_datetime(
            reference_time
        ).prefetch_related("user")

        count = 0
        for share_owner in share_owners:
            status_change_log_entry = (
                UpdateShiftUserDataLogEntry.objects.filter(
                    user=share_owner.user,
                    created_date__lte=reference_time,
                    new_values__is_frozen="True",
                )
                .order_by("-created_date")
                .first()
            )

            if status_change_log_entry:
                if (
                    reference_time - status_change_log_entry.created_date
                ).days > 30 * 6:
                    count += 1
                continue

            status_change_log_entry = (
                UpdateShiftUserDataLogEntry.objects.filter(
                    user=share_owner.user,
                    created_date__lte=reference_time,
                    new_values__attendance_mode=ShiftAttendanceMode.FROZEN,
                )
                .order_by("-created_date")
                .first()
            )

            if status_change_log_entry:
                if (
                    reference_time - status_change_log_entry.created_date
                ).days > 30 * 6:
                    count += 1
                continue

            # could not find any log entry, we assume the member is frozen long-term
            count += 1

        return count

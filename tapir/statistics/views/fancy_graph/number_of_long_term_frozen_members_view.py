import datetime

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.models import UpdateShiftUserDataLogEntry
from tapir.statistics.views.fancy_graph.base_view import DatapointView
from tapir.statistics.views.fancy_graph.number_of_frozen_members_view import (
    NumberOfFrozenMembersAtDateView,
)


class NumberOfLongTermFrozenMembersAtDateView(DatapointView):
    permission_required = PERMISSION_COOP_MANAGE

    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        share_owners_frozen = (
            NumberOfFrozenMembersAtDateView.get_members_frozen_at_datetime(
                reference_time
            )
        )
        tapir_user_frozen_ids = list(
            share_owners_frozen.values_list("user__id", flat=True)
        )

        long_term_frozen_ids = []
        for tapir_user_id in tapir_user_frozen_ids:
            status_change_log_entry = (
                UpdateShiftUserDataLogEntry.objects.filter(
                    user__id=tapir_user_id,
                    created_date__lte=reference_time,
                    new_values__is_frozen="True",
                )
                .order_by("-created_date")
                .first()
            )

            if not status_change_log_entry:
                # could not find any log entry, we assume the member is frozen long-term
                long_term_frozen_ids.append(tapir_user_id)
                continue

            if (reference_time - status_change_log_entry.created_date).days > 30 * 6:
                long_term_frozen_ids.append(tapir_user_id)

        return ShareOwner.objects.filter(user__id__in=long_term_frozen_ids)

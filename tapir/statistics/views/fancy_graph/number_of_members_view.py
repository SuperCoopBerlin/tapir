import datetime

from django.db.models import QuerySet

from tapir.coop.models import MemberStatus, ShareOwner
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfMembersAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()
        share_owner_ids = set()
        for member_status in [
            MemberStatus.ACTIVE,
            MemberStatus.PAUSED,
            MemberStatus.INVESTING,
        ]:
            share_owner_ids.update(
                ShareOwner.objects.with_status(member_status, reference_date)
                .distinct()
                .values_list("id", flat=True)
            )
        return ShareOwner.objects.filter(id__in=share_owner_ids)

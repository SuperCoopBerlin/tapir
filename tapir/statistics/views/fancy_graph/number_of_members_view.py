import datetime

from tapir.coop.models import MemberStatus, ShareOwner
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfMembersAtDateView(DatapointView):
    def get_datapoint(self, reference_time: datetime.datetime) -> int:
        reference_date = reference_time.date()
        total_count = 0
        for member_status in [
            MemberStatus.ACTIVE,
            MemberStatus.PAUSED,
            MemberStatus.INVESTING,
        ]:
            total_count += ShareOwner.objects.with_status(
                member_status, reference_date
            ).count()
        return total_count

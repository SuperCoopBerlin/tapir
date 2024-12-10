import datetime

from tapir.coop.models import MembershipResignation
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfPendingResignationsAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        reference_date = reference_time.date()

        return (
            MembershipResignation.objects.filter(
                cancellation_date__lte=reference_date, pay_out_day__gte=reference_date
            )
            .distinct()
            .count()
        )

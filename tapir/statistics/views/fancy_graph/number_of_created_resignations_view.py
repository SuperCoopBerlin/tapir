import datetime

from tapir.coop.models import MembershipResignation
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfCreatedResignationsInSameMonthView(DatapointView):
    def get_datapoint(self, reference_time: datetime.datetime) -> int:
        reference_date = reference_time.date()

        return MembershipResignation.objects.filter(
            cancellation_date__year=reference_date.year,
            cancellation_date__month=reference_date.month,
        ).count()

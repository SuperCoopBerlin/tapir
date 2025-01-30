import datetime

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfInvestingMembersAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        return ShareOwner.objects.with_status(MemberStatus.INVESTING, reference_date)

import datetime

from django.db.models import QuerySet

from tapir.coop.models import MembershipResignation, ShareOwner
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfCreatedResignationsInSameMonthView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        resignations = MembershipResignation.objects.filter(
            cancellation_date__year=reference_date.year,
            cancellation_date__month=reference_date.month,
        ).distinct()
        return ShareOwner.objects.filter(share_owner__in=resignations)

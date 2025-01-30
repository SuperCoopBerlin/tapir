import datetime

from django.db.models import QuerySet

from tapir.coop.models import MembershipResignation, ShareOwner
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfPendingResignationsAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        pending_resignations = MembershipResignation.objects.filter(
            cancellation_date__lte=reference_date, pay_out_day__gte=reference_date
        )
        return ShareOwner.objects.filter(share_owner__in=pending_resignations)

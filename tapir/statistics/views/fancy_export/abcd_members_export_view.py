import datetime

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner
from tapir.statistics.views.fancy_export.base_view import DatapointExportView
from tapir.statistics.views.fancy_graph.number_of_abcd_members_view import (
    NumberOfAbcdMembersAtDateView,
)


class AbcdMembersExportView(DatapointExportView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        return NumberOfAbcdMembersAtDateView().get_queryset(reference_time)

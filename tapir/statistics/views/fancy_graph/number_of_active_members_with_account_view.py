import datetime

from django.db.models import QuerySet

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfActiveMembersWithAccountAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()
        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_date
        ).distinct()
        active_members_with_account = TapirUser.objects.filter(
            share_owner__in=active_members, date_joined__lte=reference_date
        )
        return ShareOwner.objects.filter(user__in=active_members_with_account)

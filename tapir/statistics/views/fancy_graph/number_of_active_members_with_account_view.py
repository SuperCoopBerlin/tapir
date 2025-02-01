import datetime

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfActiveMembersWithAccountAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        reference_date = reference_time.date()
        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_date
        ).distinct()
        active_members_with_account = TapirUser.objects.filter(
            share_owner__in=active_members, date_joined__lte=reference_date
        )
        return active_members_with_account.count()

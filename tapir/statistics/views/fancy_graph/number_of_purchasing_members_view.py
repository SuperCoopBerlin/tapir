from tapir.coop.models import ShareOwner
from tapir.coop.services.investing_status_service import InvestingStatusService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfPurchasingMembersAtDateView(DatapointView):
    def get_datapoint(self, reference_time) -> int:
        return len(self.get_purchasing_members(reference_time))

    @staticmethod
    def get_purchasing_members(reference_time):
        reference_date = reference_time.date()

        share_owners = (
            ShareOwner.objects.all()
            .prefetch_related("user")
            .prefetch_related("user__shift_user_data")
            .prefetch_related("share_ownerships")
        )
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            share_owners, reference_date
        )
        share_owners = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, reference_date
            )
        )
        share_owners = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
            share_owners, reference_time
        )
        share_owners = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            share_owners, reference_time
        )

        return [
            share_owner
            for share_owner in share_owners
            if share_owner.can_shop(reference_time)
        ]

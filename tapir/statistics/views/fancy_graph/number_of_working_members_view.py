import datetime

from tapir.coop.models import ShareOwner
from tapir.coop.services.investing_status_service import InvestingStatusService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfWorkingMembersAtDateView(DatapointView):
    def get_datapoint(self, reference_time: datetime.datetime):
        reference_date = reference_time.date()

        shift_user_datas = (
            ShiftUserData.objects.filter(user__share_owner__isnull=False)
            .prefetch_related("user")
            .prefetch_related("user__share_owner")
            .prefetch_related("user__share_owner__share_ownerships")
            .prefetch_related("shift_exemptions")
        )
        shift_user_datas = FrozenStatusHistoryService.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
            shift_user_datas, reference_time
        )
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            ShareOwner.objects.all(), reference_date
        )
        share_owners = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, reference_date
            )
        )
        share_owners = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
            share_owners, reference_time
        )
        share_owners = {share_owner.id: share_owner for share_owner in share_owners}
        for shift_user_data in shift_user_datas:
            self.transfer_attributes(
                share_owners[shift_user_data.user.share_owner.id],
                shift_user_data.user.share_owner,
                [
                    NumberOfSharesService.ANNOTATION_NUMBER_OF_ACTIVE_SHARES,
                    NumberOfSharesService.ANNOTATION_SHARES_ACTIVE_AT_DATE,
                    MembershipPauseService.ANNOTATION_HAS_ACTIVE_PAUSE,
                    MembershipPauseService.ANNOTATION_HAS_ACTIVE_PAUSE_AT_DATE,
                    InvestingStatusService.ANNOTATION_WAS_INVESTING,
                    InvestingStatusService.ANNOTATION_WAS_INVESTING_AT_DATE,
                ],
            )

        return len(
            [
                shift_user_data
                for shift_user_data in shift_user_datas
                if ShiftExpectationService.is_member_expected_to_do_shifts(
                    shift_user_data, reference_time
                )
            ]
        )

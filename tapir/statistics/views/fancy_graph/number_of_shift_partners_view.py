from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.shift_partner_history_service import (
    ShiftPartnerHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfShiftPartnersAtDateView(DatapointView):
    def get_datapoint(self, reference_time) -> int:
        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_time
        )
        shift_user_datas = ShiftUserData.objects.filter(
            user__share_owner__in=active_members
        )

        shift_user_datas = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            shift_user_datas, reference_time
        )
        shift_user_datas = shift_user_datas.filter(
            **{ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER: True}
        )

        return shift_user_datas.count()
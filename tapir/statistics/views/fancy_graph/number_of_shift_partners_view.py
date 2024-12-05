from tapir.shifts.services.shift_partner_history_service import (
    ShiftPartnerHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import (
    DatapointView,
    get_shift_user_datas_of_working_members_annotated_with_attendance_mode,
)


class NumberOfShiftPartnersAtDateView(DatapointView):
    def get_datapoint(self, reference_time) -> int:
        shift_user_datas = (
            get_shift_user_datas_of_working_members_annotated_with_attendance_mode(
                reference_time
            )
        )

        shift_user_datas = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            shift_user_datas, reference_time
        )
        shift_user_datas = shift_user_datas.filter(
            **{ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER: True}
        )

        return shift_user_datas.count()

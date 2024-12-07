from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.shifts.services.shift_partner_history_service import (
    ShiftPartnerHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import (
    DatapointView,
)


class NumberOfShiftPartnersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time) -> int:
        shift_user_datas = ShiftUserData.objects.all()

        shift_user_datas = (
            ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
                shift_user_datas, reference_time
            )
        ).filter(**{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True})

        shift_user_datas = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            shift_user_datas, reference_time
        )
        shift_user_datas = shift_user_datas.filter(
            **{ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER: True}
        )

        return shift_user_datas.count()

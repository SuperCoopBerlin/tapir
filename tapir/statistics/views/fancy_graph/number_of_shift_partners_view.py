from django.db.models import Q

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
        shift_user_datas_working = (
            ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
                ShiftUserData.objects.all(), reference_time
            )
        ).filter(**{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True})
        shift_user_datas_working_ids = list(
            shift_user_datas_working.values_list("id", flat=True)
        )

        shift_user_datas_with_shift_partners = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            ShiftUserData.objects.all(), reference_time
        ).filter(
            **{ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER: True}
        )
        shift_user_datas_with_shift_partners_ids = list(
            shift_user_datas_with_shift_partners.values_list("id", flat=True)
        )

        return (
            ShiftUserData.objects.filter(
                Q(id__in=shift_user_datas_working_ids)
                & Q(id__in=shift_user_datas_with_shift_partners_ids)
            )
            .distinct()
            .count()
        )

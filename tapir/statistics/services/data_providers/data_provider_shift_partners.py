import datetime

from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.shifts.services.shift_partner_history_service import (
    ShiftPartnerHistoryService,
)
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderShiftPartners(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Shift partners")

    @classmethod
    def get_description(cls):
        return _(
            "Counted out of working members only: a frozen member with a shift partner is not counted"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
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

        shift_user_datas_with_shift_partners = ShiftUserData.objects.filter(
            Q(id__in=shift_user_datas_working_ids)
            & Q(id__in=shift_user_datas_with_shift_partners_ids)
        )
        return ShareOwner.objects.filter(
            user__shift_user_data__in=shift_user_datas_with_shift_partners
        )

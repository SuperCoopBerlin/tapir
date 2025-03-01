import datetime

from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftUserData, ShiftAttendanceMode
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider
from tapir.statistics.services.data_providers.data_provider_abcd_members import (
    DataProviderAbcdMembers,
)


class DataProviderFlyingMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Flying members")

    @classmethod
    def get_description(cls):
        return DataProviderAbcdMembers.get_description()

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        shift_user_datas = ShiftUserData.objects.all()

        shift_user_datas_working = (
            ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
                shift_user_datas, reference_time
            )
        ).filter(**{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True})
        shift_user_datas_working_ids = list(
            shift_user_datas_working.values_list("id", flat=True)
        )

        shift_user_datas_flying = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_time
        ).filter(
            **{
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.FLYING
            }
        )
        shift_user_datas_flying_ids = list(
            shift_user_datas_flying.values_list("id", flat=True)
        )

        return ShareOwner.objects.filter(
            Q(user__shift_user_data__id__in=shift_user_datas_working_ids)
            & Q(user__shift_user_data__id__in=shift_user_datas_flying_ids)
        )

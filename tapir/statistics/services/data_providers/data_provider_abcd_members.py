import datetime

from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftAttendanceMode, ShiftUserData
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderAbcdMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("ABCD members")

    @classmethod
    def get_description(cls):
        return _(
            "Only members who work are counted: members that are exempted, paused, frozen... are not counted"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        working_members = (
            ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
                ShiftUserData.objects.all(), reference_time
            )
        ).filter(**{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True})
        working_members_ids = list(working_members.values_list("id", flat=True))

        abcd_members = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_time
        ).filter(
            **{
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.REGULAR
            }
        )
        abcd_members_ids = list(abcd_members.values_list("id", flat=True))

        abcd_shift_user_datas = ShiftUserData.objects.filter(
            Q(id__in=working_members_ids) & Q(id__in=abcd_members_ids)
        ).distinct()
        return ShareOwner.objects.filter(
            user__shift_user_data__in=abcd_shift_user_datas
        )

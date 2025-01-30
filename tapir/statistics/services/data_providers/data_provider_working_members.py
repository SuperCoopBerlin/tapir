import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderWorkingMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Working members")

    @classmethod
    def get_description(cls):
        return _("")

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        queryset = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), reference_time
        )

        queryset = queryset.filter(
            **{ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: True}
        )

        return ShareOwner.objects.filter(user__shift_user_data__in=queryset)

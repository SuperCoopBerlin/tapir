import datetime

from django.db.models import QuerySet, Value, Case, When, Q
from django.utils import timezone

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_exemption_service import ShiftExemptionService
from tapir.utils.shortcuts import get_timezone_aware_datetime


class ShiftExpectationService:
    ANNOTATION_IS_WORKING_AT_DATE = "is_working_at_date"
    ANNOTATION_IS_WORKING_DATE_CHECK = "is_working_date_check"

    @staticmethod
    def is_member_expected_to_do_shifts(
        shift_user_data: ShiftUserData, at_datetime: datetime.datetime | None = None
    ) -> bool:
        if at_datetime is None:
            at_datetime = timezone.now()

        if (
            not hasattr(shift_user_data.user, "share_owner")
            or shift_user_data.user.share_owner is None
        ):
            return False

        if FrozenStatusHistoryService.is_frozen_at_datetime(
            shift_user_data, at_datetime
        ):
            return False

        if shift_user_data.user.date_joined.date() > at_datetime.date():
            return False

        if not shift_user_data.user.share_owner.is_active(at_datetime):
            return False

        if shift_user_data.is_currently_exempted_from_shifts(at_datetime.date()):
            return False

        return True

    @classmethod
    def annotate_shift_user_data_queryset_with_working_status_at_datetime(
        cls,
        shift_user_datas: QuerySet[ShiftUserData],
        reference_time: datetime.datetime,
    ):
        reference_date = reference_time.date()

        shift_user_datas_not_frozen = FrozenStatusHistoryService.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
            ShiftUserData.objects.all(), reference_time
        ).filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: False}
        )
        shift_user_datas_not_frozen_ids = list(
            shift_user_datas_not_frozen.values_list("id", flat=True)
        )

        shift_user_datas_joined_before_date = ShiftUserData.objects.filter(
            user__date_joined__lte=reference_time
        )
        joined_after_reference_time_ids = list(
            shift_user_datas_joined_before_date.values_list("id", flat=True)
        )

        active_member_ids = (
            ShareOwner.objects.filter()
            .with_status(MemberStatus.ACTIVE)
            .values_list("id", flat=True)
        )
        shift_user_data_member_active = ShiftUserData.objects.filter(
            user__share_owner__id__in=active_member_ids
        )
        shift_user_data_member_active_ids = list(
            shift_user_data_member_active.values_list("id", flat=True)
        )

        shift_user_data_not_exempted = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            ShiftUserData.objects.all(), reference_date
        ).filter(
            **{ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE: False}
        )
        shift_user_data_not_exempted_ids = list(
            shift_user_data_not_exempted.values_list("id", flat=True)
        )

        all_criteria = Q()
        for id_list in [
            shift_user_datas_not_frozen_ids,
            joined_after_reference_time_ids,
            shift_user_data_not_exempted_ids,
            shift_user_data_member_active_ids,
        ]:
            all_criteria &= Q(id__in=id_list)

        return shift_user_datas.annotate(
            **{
                ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE: Case(
                    When(
                        all_criteria,
                        then=Value(True),
                    ),
                    default=Value(False),
                ),
                ShiftExpectationService.ANNOTATION_IS_WORKING_DATE_CHECK: Value(
                    reference_time
                ),
            }
        )

    @classmethod
    def get_credit_requirement_for_cycle(
        cls, shift_user_data: ShiftUserData, cycle_start_date: datetime.date
    ):
        if not cls.is_member_expected_to_do_shifts(
            shift_user_data,
            get_timezone_aware_datetime(cycle_start_date, timezone.now().time()),
        ):
            return 0
        return 1

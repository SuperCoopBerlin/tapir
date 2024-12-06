import datetime

from django.db.models import QuerySet, Value, Case, When
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

        # not frozen
        working_shift_user_datas = FrozenStatusHistoryService.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
            shift_user_datas, reference_time
        ).filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: False}
        )

        # joined before date
        working_shift_user_datas = working_shift_user_datas.filter(
            user__date_joined__lte=reference_date
        )

        # member status active
        active_member_ids = (
            ShareOwner.objects.filter(
                user__shift_user_data__in=working_shift_user_datas
            )
            .with_status(MemberStatus.ACTIVE)
            .values_list("id", flat=True)
        )
        working_shift_user_datas = working_shift_user_datas.filter(
            user__share_owner__id__in=active_member_ids
        )

        # not exempted
        working_shift_user_datas = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            working_shift_user_datas, reference_date
        ).filter(
            **{ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE: False}
        )

        working_ids = working_shift_user_datas.values_list("id", flat=True)

        return shift_user_datas.annotate(
            **{
                cls.ANNOTATION_IS_WORKING_AT_DATE: Case(
                    When(id__in=working_ids, then=Value(True)), default=Value(False)
                ),
                cls.ANNOTATION_IS_WORKING_DATE_CHECK: Value(reference_time),
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

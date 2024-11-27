import datetime

from django.db.models import (
    QuerySet,
    OuterRef,
    Value,
    Subquery,
    CharField,
    Case,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from tapir.shifts.config import ATTENDANCE_MODE_REFACTOR_DATETIME
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
)
from tapir.utils.shortcuts import ensure_datetime


class FrozenStatusHistoryService:
    ANNOTATION_IS_FROZEN_AT_DATE = "is_frozen_at_date"
    ANNOTATION_IS_FROZEN_DATE_CHECK = "is_frozen_date_check"

    @classmethod
    def is_frozen_at_datetime(
        cls, shift_user_data: ShiftUserData, at_datetime: datetime.datetime = None
    ):
        if at_datetime is None:
            at_datetime = timezone.now()

        at_datetime = ensure_datetime(at_datetime)

        if not hasattr(shift_user_data, cls.ANNOTATION_IS_FROZEN_AT_DATE):
            shift_user_data = (
                cls.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
                    ShiftUserData.objects.filter(id=shift_user_data.id), at_datetime
                ).first()
            )

        annotated_date = getattr(shift_user_data, cls.ANNOTATION_IS_FROZEN_DATE_CHECK)
        if annotated_date != at_datetime:
            raise ValueError(
                f"Trying to get the frozen status at date {at_datetime}, but the queryset has been "
                f"annotated relative to {annotated_date}"
            )
        return getattr(shift_user_data, cls.ANNOTATION_IS_FROZEN_AT_DATE)

    @classmethod
    def annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
        cls,
        queryset: QuerySet,
        at_datetime: datetime.datetime,
        attendance_mode_prefix=None,
    ):
        queryset = queryset.annotate(
            **{cls.ANNOTATION_IS_FROZEN_DATE_CHECK: Value(at_datetime)}
        )
        if at_datetime < ATTENDANCE_MODE_REFACTOR_DATETIME:
            return cls._annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor(
                queryset, at_datetime, attendance_mode_prefix
            )
        return cls._annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor(
            queryset, at_datetime, attendance_mode_prefix
        )

    @classmethod
    def _annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor(
        cls,
        queryset: QuerySet,
        at_datetime: datetime.datetime = None,
        attendance_mode_prefix=None,
    ):
        queryset = queryset.annotate(
            attendance_mode_from_log_entry=Subquery(
                UpdateShiftUserDataLogEntry.objects.filter(
                    user_id=OuterRef("user_id"),
                    created_date__gte=at_datetime,
                )
                .order_by("created_date")
                .values("old_values__attendance_mode")[:1],
                output_field=CharField(),
            )
        )

        return queryset.annotate(
            is_frozen_at_date=Case(
                When(
                    attendance_mode_from_log_entry=ShiftAttendanceMode.FROZEN,
                    then=Value(True),
                ),
                default=(
                    "is_frozen"
                    if not attendance_mode_prefix
                    else f"{attendance_mode_prefix}__is_frozen"
                ),
            )
        )

    @classmethod
    def _annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor(
        cls,
        queryset: QuerySet,
        at_datetime: datetime.datetime = None,
        attendance_mode_prefix=None,
    ):
        queryset = queryset.annotate(
            is_frozen_from_log_entry_as_string=Subquery(
                UpdateShiftUserDataLogEntry.objects.filter(
                    user_id=OuterRef("user_id"),
                    created_date__gte=at_datetime,
                )
                .order_by("created_date")
                .values("old_values__is_frozen")[:1],
                output_field=CharField(),
            )
        )

        queryset = queryset.annotate(
            is_frozen_from_log_entry_as_bool=Case(
                When(is_frozen_from_log_entry_as_string="True", then=True),
                When(is_frozen_from_log_entry_as_string="False", then=False),
                default=None,
            )
        )

        return queryset.annotate(
            is_frozen_at_date=Coalesce(
                "is_frozen_from_log_entry_as_bool",
                (
                    "is_frozen"
                    if attendance_mode_prefix is None
                    else f"{attendance_mode_prefix}__is_frozen"
                ),
            ),
        )

    @classmethod
    def annotate_share_owner_queryset_with_is_frozen_at_datetime(
        cls, queryset: QuerySet, at_datetime: datetime.datetime = None
    ):
        return cls.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
            queryset, at_datetime, "user__shift_user_data"
        )

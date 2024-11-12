import datetime

from django.db.models import (
    QuerySet,
    OuterRef,
    Value,
    Subquery,
    CharField,
    Case,
    When,
    Count,
    F,
    Q,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
    CreateShiftAttendanceTemplateLogEntry,
)
from tapir.utils.shortcuts import ensure_date


class ShiftAttendanceModeService:
    ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE = "attendance_mode_at_date"
    ANNOTATION_SHIFT_ATTENDANCE_MODE_DATE_CHECK = "attendance_mode_date_check"
    ANNOTATION_IS_FROZEN_AT_DATE = "is_frozen_at_date"
    ANNOTATION_IS_FROZEN_DATE_CHECK = "is_frozen_date_check"
    ATTENDANCE_MODE_REFACTOR_DATE = datetime.date(year=2024, month=11, day=11)

    @classmethod
    def get_attendance_mode(
        cls, shift_user_data: ShiftUserData, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        at_date = ensure_date(at_date)

        if not hasattr(shift_user_data, cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE):
            shift_user_data = (
                cls.annotate_shift_user_data_queryset_with_attendance_mode_at_date(
                    ShiftUserData.objects.filter(id=shift_user_data.id), at_date
                ).first()
            )

        annotated_date = getattr(
            shift_user_data, cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_DATE_CHECK
        )
        if annotated_date != at_date:
            raise ValueError(
                f"Trying to get the investing status at date {at_date}, but the queryset has been "
                f"annotated relative to {annotated_date}"
            )
        return getattr(shift_user_data, cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE)

    @classmethod
    def is_frozen_at_date(
        cls, shift_user_data: ShiftUserData, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        at_date = ensure_date(at_date)

        if not hasattr(shift_user_data, cls.ANNOTATION_IS_FROZEN_AT_DATE):
            shift_user_data = (
                cls.annotate_shift_user_data_queryset_with_is_frozen_at_date(
                    ShiftUserData.objects.filter(id=shift_user_data.id), at_date
                ).first()
            )

        annotated_date = getattr(shift_user_data, cls.ANNOTATION_IS_FROZEN_DATE_CHECK)
        if annotated_date != at_date:
            raise ValueError(
                f"Trying to get the frozen status at date {at_date}, but the queryset has been "
                f"annotated relative to {annotated_date}"
            )
        return getattr(shift_user_data, cls.ANNOTATION_IS_FROZEN_AT_DATE)

    @classmethod
    def annotate_shift_user_data_queryset_with_is_frozen_at_date(
        cls, queryset: QuerySet, at_date: datetime.date, attendance_mode_prefix=None
    ):
        queryset = queryset.annotate(
            **{cls.ANNOTATION_IS_FROZEN_DATE_CHECK: Value(at_date)}
        )
        if at_date < cls.ATTENDANCE_MODE_REFACTOR_DATE:
            return cls._annotate_shift_user_data_queryset_with_is_frozen_at_date_before_refactor(
                queryset, at_date
            )
        return cls._annotate_shift_user_data_queryset_with_is_frozen_at_date_after_refactor(
            queryset, at_date, attendance_mode_prefix
        )

    @classmethod
    def _annotate_shift_user_data_queryset_with_is_frozen_at_date_before_refactor(
        cls, queryset: QuerySet, at_date: datetime.date = None
    ):
        from tapir.shifts.models import UpdateShiftUserDataLogEntry

        queryset = queryset.annotate(
            attendance_mode_from_log_entry=Subquery(
                UpdateShiftUserDataLogEntry.objects.filter(
                    user_id=OuterRef("user_id"),
                    created_date__gte=at_date,
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
                default=Value(False),
            )
        )

    @classmethod
    def _annotate_shift_user_data_queryset_with_is_frozen_at_date_after_refactor(
        cls,
        queryset: QuerySet,
        at_date: datetime.date = None,
        attendance_mode_prefix=None,
    ):
        queryset = queryset.annotate(
            is_frozen_from_log_entry_as_string=Subquery(
                UpdateShiftUserDataLogEntry.objects.filter(
                    user_id=OuterRef("user_id"),
                    created_date__gte=at_date,
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
    def _annotate_queryset_with_has_abcd_attendance_at_date(
        cls, queryset: QuerySet, at_date: datetime.date
    ):
        queryset = queryset.annotate(
            nb_attendance_template_create=Count(
                "user__log_entries",
                filter=Q(
                    user__log_entries__log_class_type__model=CreateShiftAttendanceTemplateLogEntry.__name__.lower(),
                    user__log_entries__created_date__lte=at_date,
                ),
            ),
            nb_attendance_template_delete=Count(
                "user__log_entries",
                filter=Q(
                    user__log_entries__log_class_type__model=DeleteShiftAttendanceTemplateLogEntry.__name__.lower(),
                    user__log_entries__created_date__lte=at_date,
                ),
            ),
        )

        queryset = queryset.annotate(
            has_abcd_attendance_at_date=Case(
                When(
                    nb_attendance_template_create__gt=F(
                        "nb_attendance_template_delete"
                    ),
                    then=Value(True),
                ),
                default=Value(False),
            ),
        )

        return queryset

    @classmethod
    def annotate_shift_user_data_queryset_with_attendance_mode_at_date(
        cls,
        queryset: QuerySet,
        at_date: datetime.date = None,
        attendance_mode_prefix=None,
    ):
        if at_date is None:
            at_date = timezone.now().date()

        queryset = cls.annotate_shift_user_data_queryset_with_is_frozen_at_date(
            queryset, at_date, attendance_mode_prefix
        )

        queryset = cls._annotate_queryset_with_has_abcd_attendance_at_date(
            queryset, at_date
        )

        annotate_kwargs = {
            cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: Case(
                When(is_frozen_at_date=True, then=Value(ShiftAttendanceMode.FROZEN)),
                When(
                    has_abcd_attendance_at_date=True,
                    then=Value(ShiftAttendanceMode.REGULAR),
                ),
                default=Value(ShiftAttendanceMode.FLYING),
            ),
            cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_DATE_CHECK: Value(at_date),
        }
        return queryset.annotate(**annotate_kwargs)

    @classmethod
    def annotate_share_owner_queryset_with_attendance_mode_at_date(
        cls, queryset: QuerySet, at_date: datetime.date = None
    ):
        return cls.annotate_shift_user_data_queryset_with_attendance_mode_at_date(
            queryset, at_date, "user__shift_user_data"
        )

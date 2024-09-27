import datetime

from django.db.models import QuerySet, OuterRef, Value, Subquery, CharField
from django.db.models.functions import Coalesce
from django.utils import timezone

from tapir.shifts.models import ShiftUserData


class ShiftAttendanceModeService:
    ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE = "attendance_mode_at_date"
    ANNOTATION_SHIFT_ATTENDANCE_MODE_DATE_CHECK = "attendance_mode_date_check"

    @classmethod
    def get_attendance_mode(
        cls, shift_user_data: ShiftUserData, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        if not hasattr(shift_user_data, cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE):
            shift_user_data = (
                cls.annotate_share_owner_queryset_with_investing_status_at_date(
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
    def annotate_shift_user_data_queryset_with_attendance_mode_at_date(
        cls, queryset: QuerySet, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

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

        annotate_kwargs = {
            cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: Coalesce(
                "attendance_mode_from_log_entry",
                "attendance_mode",
            ),
            cls.ANNOTATION_SHIFT_ATTENDANCE_MODE_DATE_CHECK: Value(at_date),
        }
        return queryset.annotate(**annotate_kwargs)

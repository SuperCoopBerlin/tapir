import datetime

from django.db.models import QuerySet, Q, Count, Value, Case, When
from django.utils import timezone

from tapir.shifts.models import ShiftUserData
from tapir.utils.shortcuts import ensure_date


class ShiftExemptionService:
    ANNOTATION_HAS_EXEMPTION_AT_DATE = "has_exemption_at_date"
    ANNOTATION_HAS_EXEMPTION_DATE_CHECK = "has_exemption_date_check"

    @classmethod
    def annotate_shift_user_data_queryset_with_has_exemption_at_date(
        cls, queryset: QuerySet[ShiftUserData], reference_date: datetime.date
    ):
        if reference_date is None:
            reference_date = timezone.now().date()
        reference_date = ensure_date(reference_date)

        filters = Q(shift_exemptions__start_date__lte=reference_date) & (
            Q(shift_exemptions__end_date__gte=reference_date)
            | Q(shift_exemptions__end_date__isnull=True)
        )

        queryset = queryset.annotate(
            nb_active_exemptions=Count("shift_exemptions", filter=filters)
        )

        annotate_kwargs = {
            cls.ANNOTATION_HAS_EXEMPTION_AT_DATE: Case(
                When(nb_active_exemptions__gt=0, then=Value(True)), default=Value(False)
            ),
            cls.ANNOTATION_HAS_EXEMPTION_DATE_CHECK: Value(reference_date),
        }
        return queryset.annotate(**annotate_kwargs)

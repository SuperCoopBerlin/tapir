from __future__ import annotations

import datetime

from django.db.models import (
    Value,
    OuterRef,
    Case,
    When,
    QuerySet,
    Subquery,
    Exists,
)
from django.db.models.fields import CharField
from django.utils import timezone

from tapir.shifts.models import ShiftUserData, UpdateShiftUserDataLogEntry


class ShiftPartnerHistoryService:
    ANNOTATION_HAS_SHIFT_PARTNER = "has_shift_partner"
    ANNOTATION_HAS_SHIFT_PARTNER_DATE_CHECK = "has_shift_partner_date_check"

    @classmethod
    def has_shift_partner(
        cls, shift_user_data: ShiftUserData, at_datetime: datetime.datetime = None
    ):
        if at_datetime is None:
            at_datetime = timezone.now()

        if not hasattr(shift_user_data, cls.ANNOTATION_HAS_SHIFT_PARTNER):
            shift_user_data = (
                cls.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
                    ShiftUserData.objects.filter(id=shift_user_data.id), at_datetime
                ).first()
            )

        annotated_date = getattr(
            shift_user_data, cls.ANNOTATION_HAS_SHIFT_PARTNER_DATE_CHECK
        )
        if annotated_date != at_datetime:
            raise ValueError(
                f"Trying to get 'has shift partner' at date {at_datetime}, but the queryset has been "
                f"annotated relative to {annotated_date}"
            )
        return getattr(shift_user_data, cls.ANNOTATION_HAS_SHIFT_PARTNER)

    @classmethod
    def annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
        cls,
        queryset: QuerySet[ShiftUserData],
        at_datetime: datetime.datetime = None,
    ):
        if at_datetime is None:
            at_datetime = timezone.now()

        relevant_logs = UpdateShiftUserDataLogEntry.objects.filter(
            user_id=OuterRef("user_id"),
            created_date__gte=at_datetime,
            old_values__has_key="shift_partner",
        )
        subquery_shift_partner_from_log = Subquery(
            relevant_logs.order_by("created_date").values("old_values__shift_partner")[
                :1
            ],
            output_field=CharField(),
        )

        queryset = queryset.annotate(
            shift_partner_from_log=subquery_shift_partner_from_log,
            shift_partner_log_found=Exists(relevant_logs),
        )

        return queryset.annotate(
            **{
                cls.ANNOTATION_HAS_SHIFT_PARTNER: Case(
                    When(
                        shift_partner_log_found=True,
                        then=Case(
                            When(
                                shift_partner_from_log=None,
                                then=False,
                            ),
                            default=True,
                        ),
                    ),
                    default=Case(When(shift_partner=None, then=False), default=True),
                ),
                cls.ANNOTATION_HAS_SHIFT_PARTNER_DATE_CHECK: Value(at_datetime),
            },
        )

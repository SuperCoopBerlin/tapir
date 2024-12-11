from __future__ import annotations

import datetime

from django.db.models import (
    Value,
    OuterRef,
    Case,
    When,
    QuerySet,
    Q,
    CharField,
    Subquery,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from tapir.accounts.models import TapirUser, UpdateTapirUserLogEntry


class CoPurchaserHistoryService:
    ANNOTATION_HAS_CO_PURCHASER = "has_co_purchaser"
    ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK = "has_co_purchaser_date_check"

    @classmethod
    def annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
        cls,
        queryset: QuerySet[TapirUser],
        at_datetime: datetime.datetime = None,
    ):
        if at_datetime is None:
            at_datetime = timezone.now()

        queryset = queryset.annotate(
            co_purchaser_from_log_entry=Subquery(
                UpdateTapirUserLogEntry.objects.filter(
                    user_id=OuterRef("id"),
                    created_date__gte=at_datetime,
                    old_values__has_key="co_purchaser",
                )
                .order_by("created_date")
                .values("old_values__co_purchaser")[:1],
                output_field=CharField(),
            )
        )

        queryset = queryset.annotate(
            co_purchaser_at_date=Coalesce("co_purchaser_from_log_entry", "co_purchaser")
        )

        return queryset.annotate(
            **{
                cls.ANNOTATION_HAS_CO_PURCHASER: Case(
                    When(~Q(co_purchaser_at_date=""), then=True), default=False
                ),
                cls.ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK: Value(at_datetime),
            },
        )

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
    def has_co_purchaser(
        cls, tapir_user: TapirUser, at_datetime: datetime.datetime = None
    ):
        if at_datetime is None:
            at_datetime = timezone.now()

        if not hasattr(tapir_user, cls.ANNOTATION_HAS_CO_PURCHASER):
            tapir_user = cls.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
                TapirUser.objects.filter(id=tapir_user.id), at_datetime
            ).first()

        annotated_date = getattr(tapir_user, cls.ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK)
        if annotated_date != at_datetime:
            raise ValueError(
                f"Trying to get 'has co purchaser' at date {at_datetime}, but the queryset has been "
                f"annotated relative to {annotated_date}"
            )
        return getattr(tapir_user, cls.ANNOTATION_HAS_CO_PURCHASER)

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
                    created_date__lte=at_datetime,
                    new_values__co_purchaser__isnull=False,
                )
                .order_by("-created_date")
                .values("new_values__co_purchaser")[:1],
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

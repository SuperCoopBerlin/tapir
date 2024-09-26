from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from django.db.models import Value, OuterRef, Q, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone

if TYPE_CHECKING:
    from tapir.coop.models import ShareOwner


class InvestingStatusService:
    ANNOTATION_WAS_INVESTING = "was_investing"
    ANNOTATION_WAS_INVESTING_AT_DATE = "was_investing_date_check"

    @classmethod
    def is_investing(cls, share_owner: ShareOwner, at_date: datetime.date = None):
        if at_date is None:
            at_date = timezone.now().date()

        if not hasattr(share_owner, cls.ANNOTATION_WAS_INVESTING):
            from tapir.coop.models import ShareOwner

            share_owner = (
                cls.annotate_share_owner_queryset_with_investing_status_at_date(
                    ShareOwner.objects.filter(id=share_owner.id), at_date
                ).first()
            )

        annotated_date = getattr(share_owner, cls.ANNOTATION_WAS_INVESTING_AT_DATE)
        if annotated_date != at_date:
            raise ValueError(
                f"Trying to get the investing status at date {at_date}, but the queryset has been "
                f"annotated relative to {annotated_date}"
            )
        return getattr(share_owner, cls.ANNOTATION_WAS_INVESTING)

    @classmethod
    def annotate_share_owner_queryset_with_investing_status_at_date(
        cls, queryset: ShareOwner.ShareOwnerQuerySet, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        from tapir.coop.models import UpdateShareOwnerLogEntry

        queryset = queryset.annotate(
            was_investing_as_string=UpdateShareOwnerLogEntry.objects.filter(
                Q(share_owner_id=OuterRef("id")) | Q(user_id=OuterRef("user_id")),
                created_date__gte=at_date,
            )
            .order_by("created_date")
            .values("old_values__is_investing")[:1]
        )

        queryset = queryset.annotate(
            was_investing_as_bool=Case(
                When(was_investing_as_string__startswith="True", then=True),
                When(was_investing_as_string__startswith="False", then=False),
                default=None,
            )
        )

        annotate_kwargs = {
            cls.ANNOTATION_WAS_INVESTING: Coalesce(
                "was_investing_as_bool",
                "is_investing",
            ),
            cls.ANNOTATION_WAS_INVESTING_AT_DATE: Value(at_date),
        }
        return queryset.annotate(**annotate_kwargs)

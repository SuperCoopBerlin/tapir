from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from django.db.models import Count, Q, Value
from django.utils import timezone

if TYPE_CHECKING:
    from tapir.coop.models import ShareOwner


class NumberOfSharesService:
    ANNOTATION_NUMBER_OF_ACTIVE_SHARES = "num_active_shares"
    ANNOTATION_SHARES_ACTIVE_AT_DATE = "shares_active_date_check"

    @classmethod
    def get_number_of_active_shares(
        cls, share_owner: ShareOwner, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        if not hasattr(share_owner, cls.ANNOTATION_NUMBER_OF_ACTIVE_SHARES):
            return share_owner.share_ownerships.active_temporal(at_date).count()

        annotated_active_date = getattr(
            share_owner, cls.ANNOTATION_SHARES_ACTIVE_AT_DATE
        )
        if annotated_active_date != at_date:
            raise ValueError(
                f"Trying to get the number of shares active at date {at_date}, but the queryset has been "
                f"annotated relative to {annotated_active_date}"
            )
        return getattr(share_owner, cls.ANNOTATION_NUMBER_OF_ACTIVE_SHARES)

    @classmethod
    def annotate_share_owner_queryset_with_nb_of_active_shares(
        cls, queryset: ShareOwner.ShareOwnerQuerySet, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        filters = Q(share_ownerships__start_date__lte=at_date) & (
            Q(share_ownerships__end_date__gte=at_date)
            | Q(share_ownerships__end_date__isnull=True)
        )

        annotate_kwargs = {
            cls.ANNOTATION_NUMBER_OF_ACTIVE_SHARES: Count(
                "share_ownerships", filter=filters
            ),
            cls.ANNOTATION_SHARES_ACTIVE_AT_DATE: Value(at_date),
        }
        return queryset.annotate(**annotate_kwargs)

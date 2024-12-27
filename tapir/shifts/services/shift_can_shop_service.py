from __future__ import annotations

import datetime
import typing

from django.db.models import QuerySet, Case, When, Value

from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)

if typing.TYPE_CHECKING:
    from tapir.coop.models import ShareOwner


class ShiftCanShopService:
    ANNOTATION_SHIFT_CAN_SHOP = "shift_can_shop"
    ANNOTATION_SHIFT_CAN_SHOP_DATE_CHECK = "shift_can_shop_date_check"

    @classmethod
    def can_shop(
        cls,
        member_object: ShiftUserData | ShareOwner,
        at_datetime: datetime.datetime = None,
    ):
        return not FrozenStatusHistoryService.is_frozen_at_datetime(
            member_object, at_datetime
        )

    @classmethod
    def annotate_share_owner_queryset_with_can_shop_at_datetime(
        cls, share_owners: QuerySet[ShareOwner], reference_datetime: datetime.datetime
    ):
        share_owners_frozen = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            share_owners, reference_datetime
        ).filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: True}
        )
        share_owners_frozen_ids = list(share_owners_frozen.values_list("id", flat=True))

        return share_owners.annotate(
            **{
                cls.ANNOTATION_SHIFT_CAN_SHOP: Case(
                    When(
                        id__in=share_owners_frozen_ids,
                        then=False,
                    ),
                    default=True,
                ),
                cls.ANNOTATION_SHIFT_CAN_SHOP_DATE_CHECK: Value(reference_datetime),
            }
        )

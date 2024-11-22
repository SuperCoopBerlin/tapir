from __future__ import annotations

import datetime
import typing

from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)

if typing.TYPE_CHECKING:
    from tapir.coop.models import ShareOwner


class ShiftCanShopService:
    @classmethod
    def can_shop(
        cls,
        member_object: ShiftUserData | ShareOwner,
        at_datetime: datetime.datetime = None,
    ):
        return not FrozenStatusHistoryService.is_frozen_at_datetime(
            member_object, at_datetime
        )

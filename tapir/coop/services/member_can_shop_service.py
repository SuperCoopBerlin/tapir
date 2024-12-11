import datetime

from django.db.models import QuerySet, Case, When, Value

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_can_shop_service import ShiftCanShopService


class MemberCanShopService:
    ANNOTATION_CAN_SHOP = "can_shop_at_date"
    ANNOTATION_CAN_SHOP_DATE_CHECK = "can_shop_date_check"

    @staticmethod
    def can_shop(
        share_owner: ShareOwner,
        at_datetime: datetime.datetime | datetime.date | None = None,
    ):
        if share_owner.user is None:
            return False
        if not share_owner.is_active(at_datetime):
            return False

        member_object = share_owner
        if not hasattr(
            member_object, FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE
        ):
            member_object = share_owner.user.shift_user_data

        return ShiftCanShopService.can_shop(member_object, at_datetime)

    @classmethod
    def annotate_share_owner_queryset_with_shopping_status_at_datetime(
        cls, share_owners: QuerySet[ShareOwner], reference_datetime: datetime.datetime
    ):
        members_who_can_shop = share_owners.filter(user__isnull=False)
        members_who_can_shop = members_who_can_shop.with_status(
            MemberStatus.ACTIVE, reference_datetime
        )
        members_who_can_shop = (
            ShiftCanShopService.annotate_share_owner_queryset_with_can_shop_at_datetime(
                members_who_can_shop, reference_datetime
            )
        )
        members_who_can_shop = members_who_can_shop.filter(
            **{ShiftCanShopService.ANNOTATION_SHIFT_CAN_SHOP: True}
        )
        ids = members_who_can_shop.values_list("id", flat=True)

        return share_owners.annotate(
            **{
                cls.ANNOTATION_CAN_SHOP: Case(
                    When(id__in=ids, then=True), default=False
                ),
                cls.ANNOTATION_CAN_SHOP_DATE_CHECK: Value(reference_datetime),
            }
        )

import datetime

from django.db.models import QuerySet, Case, When, Value

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.services.shift_can_shop_service import ShiftCanShopService


class MemberCanShopService:
    ANNOTATION_CAN_SHOP = "can_shop_at_date"
    ANNOTATION_CAN_SHOP_DATE_CHECK = "can_shop_date_check"

    @staticmethod
    def can_shop(
        share_owner: ShareOwner,
        at_datetime: datetime.datetime | datetime.date | None = None,
    ):
        return (
            share_owner.user is not None
            and share_owner.is_active(at_datetime)
            and ShiftCanShopService.can_shop(share_owner, at_datetime)
        )

    @classmethod
    def annotate_share_owner_queryset_with_shopping_status_at_datetime(
        cls, share_owners: QuerySet[ShareOwner], reference_datetime: datetime.datetime
    ):
        members_who_can_shop = share_owners.filter(user__isnull=False)
        members_who_can_shop = members_who_can_shop.with_status(MemberStatus.ACTIVE)
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

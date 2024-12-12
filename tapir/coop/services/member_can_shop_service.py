import datetime

from django.db.models import QuerySet, Case, When, Value, Q

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
        if share_owner.user.date_joined > at_datetime:
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
        members_with_an_account = share_owners.filter(user__isnull=False)
        members_with_an_account_ids = list(
            members_with_an_account.values_list("id", flat=True)
        )

        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_datetime
        )
        active_members_ids = list(active_members.values_list("id", flat=True))

        members_who_joined_before_date = share_owners.filter(
            user__date_joined__lte=reference_datetime
        )
        members_who_joined_before_date_ids = list(
            members_who_joined_before_date.values_list("id", flat=True)
        )

        shift_can_shop_members = (
            ShiftCanShopService.annotate_share_owner_queryset_with_can_shop_at_datetime(
                ShareOwner.objects.all(), reference_datetime
            ).filter(**{ShiftCanShopService.ANNOTATION_SHIFT_CAN_SHOP: True})
        )
        shift_can_shop_members_ids = list(
            shift_can_shop_members.values_list("id", flat=True)
        )

        all_criteria = Q()
        for id_list in [
            members_with_an_account_ids,
            active_members_ids,
            members_who_joined_before_date_ids,
            shift_can_shop_members_ids,
        ]:
            all_criteria &= Q(id__in=id_list)

        return share_owners.annotate(
            **{
                cls.ANNOTATION_CAN_SHOP: Case(
                    When(all_criteria, then=True), default=False
                ),
                cls.ANNOTATION_CAN_SHOP_DATE_CHECK: Value(reference_datetime),
            }
        )

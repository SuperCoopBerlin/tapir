import datetime

from django.db.models import Q, QuerySet

from tapir.accounts.models import TapirUser
from tapir.accounts.services.co_purchaser_history_service import (
    CoPurchaserHistoryService,
)
from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfCoPurchasersAtDateView(DatapointView):
    def get_queryset(self, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        share_owners_that_can_shop = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), reference_time
        ).filter(
            **{MemberCanShopService.ANNOTATION_CAN_SHOP: True}
        )
        share_owners_that_can_shop_ids = list(
            share_owners_that_can_shop.values_list("id", flat=True)
        )

        tapir_users_with_co_purchasers = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            TapirUser.objects.all(), reference_time
        ).filter(
            **{CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER: True}
        )
        tapir_users_with_co_purchasers_ids = list(
            tapir_users_with_co_purchasers.values_list("id", flat=True)
        )

        return ShareOwner.objects.filter(
            Q(id__in=share_owners_that_can_shop_ids)
            & Q(user__id__in=tapir_users_with_co_purchasers_ids)
        )

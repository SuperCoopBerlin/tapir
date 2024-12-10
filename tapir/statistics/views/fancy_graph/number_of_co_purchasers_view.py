import datetime

from tapir.accounts.models import TapirUser
from tapir.accounts.services.co_purchaser_history_service import (
    CoPurchaserHistoryService,
)
from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfCoPurchasersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        tapir_users = TapirUser.objects.all()

        purchasing_members = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), reference_time
        )
        purchasing_members = purchasing_members.filter(
            **{MemberCanShopService.ANNOTATION_CAN_SHOP: True}
        )
        tapir_users = tapir_users.filter(share_owner__in=purchasing_members)

        tapir_users = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            tapir_users, reference_time
        )
        tapir_users = tapir_users.filter(
            **{CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER: True}
        )

        return tapir_users.distinct().count()

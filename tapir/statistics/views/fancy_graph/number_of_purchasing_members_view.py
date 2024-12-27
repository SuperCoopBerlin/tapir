from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class NumberOfPurchasingMembersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time) -> int:
        share_owners = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), reference_time
        )
        return (
            share_owners.filter(**{MemberCanShopService.ANNOTATION_CAN_SHOP: True})
            .distinct()
            .count()
        )

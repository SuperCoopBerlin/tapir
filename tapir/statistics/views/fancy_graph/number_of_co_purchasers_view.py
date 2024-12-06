import datetime

from tapir.accounts.models import TapirUser
from tapir.accounts.services.co_purchaser_history_service import (
    CoPurchaserHistoryService,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView
from tapir.statistics.views.fancy_graph.number_of_purchasing_members_view import (
    NumberOfPurchasingMembersAtDateView,
)


class NumberOfCoPurchasersAtDateView(DatapointView):
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        tapir_users = TapirUser.objects.all()
        purchasing_members = NumberOfPurchasingMembersAtDateView.get_purchasing_members(
            reference_time
        )
        tapir_users = tapir_users.filter(share_owner__in=purchasing_members)

        tapir_users = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            tapir_users, reference_time
        )
        tapir_users = tapir_users.filter(
            **{CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER: True}
        )

        return tapir_users.count()

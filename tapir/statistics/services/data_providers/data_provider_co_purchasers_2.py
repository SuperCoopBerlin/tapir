import datetime

from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.accounts.services.second_co_purchaser_history_service import (
    SecondCoPurchaserHistoryService,
)
from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderCoPurchasers2(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Second co-purchasers")

    @classmethod
    def get_description(cls):
        return _(
            "Only members who can shop are counted: members that have a second co-purchaser but are not allowed to shop are not counted"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        share_owners_that_can_shop = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), reference_time
        ).filter(
            **{MemberCanShopService.ANNOTATION_CAN_SHOP: True}
        )
        share_owners_that_can_shop_ids = list(
            share_owners_that_can_shop.values_list("id", flat=True)
        )

        tapir_users_with_co_purchasers = SecondCoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_second_co_purchaser_at_date(
            TapirUser.objects.all(), reference_time
        ).filter(
            **{SecondCoPurchaserHistoryService.ANNOTATION_HAS_SECOND_CO_PURCHASER: True}
        )
        tapir_users_with_co_purchasers_ids = list(
            tapir_users_with_co_purchasers.values_list("id", flat=True)
        )

        return ShareOwner.objects.filter(
            Q(id__in=share_owners_that_can_shop_ids)
            & Q(user__id__in=tapir_users_with_co_purchasers_ids)
        )

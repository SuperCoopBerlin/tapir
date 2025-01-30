import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderPurchasingMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Purchasing members")

    @classmethod
    def get_description(cls):
        return _(
            'Members who are allowed to shop. To be allowed to shop, a member must be active (see the description for "Active members"), have a Tapir account, and not be frozen.'
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        share_owners = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), reference_time
        )
        return share_owners.filter(**{MemberCanShopService.ANNOTATION_CAN_SHOP: True})

import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderInvestingMembers(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Investing members")

    @classmethod
    def get_description(cls):
        return _("")

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        return ShareOwner.objects.with_status(MemberStatus.INVESTING, reference_date)

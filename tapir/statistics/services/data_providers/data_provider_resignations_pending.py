import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner, MembershipResignation
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderResignationsPending(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Pending resignations")

    @classmethod
    def get_description(cls):
        return _(
            "Members who want to get their money back and are waiting for the 3 year term"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        pending_resignations = MembershipResignation.objects.filter(
            cancellation_date__lte=reference_date, pay_out_day__gte=reference_date
        )
        return ShareOwner.objects.filter(share_owner__in=pending_resignations)

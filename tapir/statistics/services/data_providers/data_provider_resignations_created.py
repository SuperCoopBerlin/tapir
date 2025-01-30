import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner, MembershipResignation
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderResignationsCreated(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Created resignations")

    @classmethod
    def get_description(cls):
        return _(
            "Regardless of whether the member gifts their share or get their money back, this is relative to when the resignation is created."
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        resignations = MembershipResignation.objects.filter(
            cancellation_date__year=reference_date.year,
            cancellation_date__month=reference_date.month,
        ).distinct()
        return ShareOwner.objects.filter(share_owner__in=resignations)

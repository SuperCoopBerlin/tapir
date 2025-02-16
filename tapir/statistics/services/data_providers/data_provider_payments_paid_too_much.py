import datetime

from django.db.models import QuerySet, F
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.coop.services.payment_status_service import PaymentStatusService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderPaymentsPaidTooMuch(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Paid too much")

    @classmethod
    def get_description(cls):
        return _(
            "Members that have paid more than expected relative to their number of shares"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        queryset = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.all(), reference_time.date()
        )

        return queryset.filter(
            **{
                f"{PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE}__gt": F(
                    PaymentStatusService.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE
                )
            }
        )

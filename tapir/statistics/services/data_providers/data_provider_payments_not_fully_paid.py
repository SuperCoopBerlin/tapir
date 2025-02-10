import datetime

from django.db.models import QuerySet, F
from django.utils.translation import gettext_lazy as _
from icecream import ic

from tapir.coop.models import ShareOwner
from tapir.coop.services.payment_status_service import PaymentStatusService
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderPaymentsNotFullyPaid(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Hasn't completed payments")

    @classmethod
    def get_description(cls):
        return _(
            "Members that have paid either nothing or not enough compared to the number of shares they subscribed to"
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        queryset = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.all(), reference_time.date()
        )
        ic(queryset.count())

        return ic(
            queryset.filter(
                **{
                    f"{PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE}__lt": F(
                        PaymentStatusService.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE
                    )
                }
            )
        )

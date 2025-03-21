import datetime

from django.db.models import QuerySet, Sum, Count, Value, Q, Subquery, OuterRef
from django.utils import timezone

from tapir.coop.config import COOP_SHARE_PRICE, COOP_ENTRY_AMOUNT
from tapir.coop.models import ShareOwner, ShareOwnership


class PaymentStatusService:
    ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE = "credited_payments_sum"
    ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE = "expected_payments_sum"
    ANNOTATION_PAYMENT_DATE_CHECK = "payments_sum_date_check"

    @classmethod
    def get_amount_paid_at_date(
        cls, share_owner: ShareOwner, at_date: datetime.date | None = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        if not hasattr(share_owner, cls.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE):
            share_owner = cls.annotate_with_payments_at_date(
                ShareOwner.objects.filter(id=share_owner.id), at_date
            ).first()

        date_check = getattr(share_owner, cls.ANNOTATION_PAYMENT_DATE_CHECK)
        if date_check != at_date:
            raise ValueError(
                f"Trying to get the credited payments at date {at_date}, but the queryset has been "
                f"annotated relative to {date_check}"
            )
        return getattr(share_owner, cls.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE)

    @classmethod
    def annotate_with_payments_at_date(
        cls, queryset: QuerySet[ShareOwner], at_date: datetime.date | None = None
    ) -> QuerySet[ShareOwner]:
        if at_date is None:
            at_date = timezone.now().date()

        # because of how annotations works, we need to use subqueries, see https://stackoverflow.com/a/56619484
        credited_payments_sum_queryset = queryset.annotate(
            **{
                cls.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE: Sum(
                    "credited_payments__amount",
                    filter=Q(credited_payments__payment_date__lte=at_date),
                    default=0,
                )
            }
        ).filter(pk=OuterRef("pk"))
        active_shares_id = ShareOwnership.objects.active_temporal(at_date).values_list(
            "id", flat=True
        )
        expected_payments_sum_queryset = queryset.annotate(
            **{
                cls.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE: Count(
                    "share_ownerships",
                    distinct=True,
                    filter=Q(share_ownerships__id__in=active_shares_id),
                )
                * COOP_SHARE_PRICE
                + COOP_ENTRY_AMOUNT,
            }
        ).filter(pk=OuterRef("pk"))

        queryset = queryset.annotate(
            **{
                cls.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE: Subquery(
                    credited_payments_sum_queryset.values(
                        cls.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE
                    )
                ),
                cls.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE: Subquery(
                    expected_payments_sum_queryset.values(
                        cls.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE
                    )
                ),
                cls.ANNOTATION_PAYMENT_DATE_CHECK: Value(at_date),
            }
        )

        return queryset

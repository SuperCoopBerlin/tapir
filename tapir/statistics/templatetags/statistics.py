from django import template
from django.db.models import Sum
from django.utils import timezone

from tapir.statistics.models import PurchaseBasket

register = template.Library()


@register.inclusion_tag(
    "statistics/tags/purchase_statistics_card.html", takes_context=True
)
def purchase_statistics_card(context, tapir_user):
    user_purchases = PurchaseBasket.objects.filter(tapir_user=tapir_user)
    context["last_purchases"] = user_purchases.order_by("-purchase_date")[:10]

    first_purchase = user_purchases.order_by("purchase_date").first()
    if not first_purchase:
        context["average_basket_per_month"] = 0
        return context

    first_purchase: PurchaseBasket
    days_since_first_purchase = (
        timezone.now().date() - first_purchase.purchase_date.date()
    ).days
    average_days_per_month = 365.25 / 12
    months_since_first_purchase = days_since_first_purchase / average_days_per_month
    context["average_basket_per_month"] = "{:.2f}".format(
        user_purchases.aggregate(total_paid=Sum("gross_amount"))["total_paid"]
        / months_since_first_purchase
    )
    return context

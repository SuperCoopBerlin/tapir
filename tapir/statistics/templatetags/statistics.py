from django import template
from django.urls import reverse

from tapir.statistics.models import PurchaseBasket
from tapir.statistics.views import get_average_monthly_basket

register = template.Library()


@register.inclusion_tag(
    "statistics/tags/purchase_statistics_card.html", takes_context=True
)
def purchase_statistics_card(context, tapir_user):
    user_purchases = PurchaseBasket.objects.filter(tapir_user=tapir_user)
    context["last_purchases"] = user_purchases.order_by("-purchase_date")[:10]
    context["average_basket_per_month"] = "{:.2f}".format(
        get_average_monthly_basket(user_purchases)
    )

    return context


@register.inclusion_tag("statistics/tags/on_demand_chart.html")
def on_demand_chart(json_view_name: str, chart_name: str):
    return {
        "chart_name": chart_name,
        "url": reverse(json_view_name),
        "prefix": json_view_name.split(":")[1],
    }

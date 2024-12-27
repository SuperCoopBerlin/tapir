from django import template
from django.urls import reverse

from tapir.statistics.models import PurchaseBasket, CreditAccount
from tapir.statistics.views import get_average_monthly_basket

from django.db.models import Sum

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


@register.inclusion_tag("statistics/tags/credit_account_card.html", takes_context=True)
def credit_account_card(context, tapir_user):
    user_credits = CreditAccount.objects.filter(tapir_user=tapir_user)
    if user_credits:
        context["last_credits"] = user_credits.order_by("-credit_date")[:10]
        context["actual_credit"] = "{:.2f}".format(
            user_credits.aggregate(total_credit=Sum("credit_amount"))["total_credit"]
        )
    return context


@register.inclusion_tag("statistics/tags/on_demand_chart.html")
def on_demand_chart(chart_name: str, json_view_name: str = None, *args):
    url = reverse(json_view_name, args=args)

    return {
        "chart_name": chart_name,
        "url": url,
        "prefix": json_view_name.split(":")[1],
    }

import datetime

from django import template

from tapir.coop.models import ShareOwner, ShareOwnership

register = template.Library()


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def share_owner_ownership_list(context, share_owner: ShareOwner):
    context["owner"] = share_owner
    return context


@register.inclusion_tag("coop/shop_extension_share_count.html", takes_context=True)
def shop_extension_share_count(context):
    nb_shares_at_start = ShareOwnership.objects.active_temporal(
        datetime.date(day=1, month=1, year=2022)
    ).count()
    nb_shares_now = ShareOwnership.objects.active_temporal().count()
    context["shop_extension_current"] = nb_shares_now - nb_shares_at_start
    context["shop_extension_max"] = 200
    context["shop_extension_progress"] = (
        context["shop_extension_current"] / context["shop_extension_max"]
    ) * 100
    return context

from django import template

from tapir.coop.config import FINANCING_INFORMATION_URL
from tapir.coop.models import (
    ShareOwner,
    FinancingCampaign,
    FinancingSource,
)

register = template.Library()


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def share_owner_ownership_list(context, share_owner: ShareOwner):
    context["share_owner"] = share_owner
    return context


@register.inclusion_tag("coop/shop_extension_progress_bar.html", takes_context=True)
def shop_extension_progress_bar(context):
    campaign = FinancingCampaign.objects.filter(is_active=True).first()
    context["FINANCING_INFORMATION_URL"] = FINANCING_INFORMATION_URL
    context["shop_extension_campaign_is_active"] = campaign is not None
    if campaign is None:
        return context

    context["shop_extension_campaign_goal"] = campaign.goal
    context["shop_extension_campaign_name"] = campaign.name

    sources = dict()
    progress_bar_colors = ["bg-primary", "bg-success", "bg-warning"]
    for source_index, source in enumerate(
        FinancingSource.objects.filter(campaign=campaign)
    ):
        source_context = dict()
        source_context["width"] = round(
            100 * float(source.raised_amount) / campaign.goal
        )
        source_context["color"] = progress_bar_colors[
            source_index % len(progress_bar_colors)
        ]
        sources[source.name] = source_context
    context["shop_extension_sources"] = sources

    return context

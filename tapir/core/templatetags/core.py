from django import template

from tapir.core.config import TAPIR_TABLE_CLASSES, sidebar_link_groups
from tapir.core.models import FeatureFlag
from tapir.financingcampaign.models import FinancingCampaign

register = template.Library()


@register.inclusion_tag("core/sidebar_links.html", takes_context=True)
def sidebar_links(context):
    request = context["request"]
    context["sidebar_link_groups"] = sidebar_link_groups.get_groups_and_links_for_user(
        request.user, request.path
    )
    return context


@register.simple_tag
def tapir_table_classes():
    return TAPIR_TABLE_CLASSES


@register.simple_tag
def tapir_button_link():
    return "btn tapir-btn btn-outline-secondary"


@register.simple_tag
def tapir_button_link_to_action():
    return "btn tapir-btn btn-outline-primary"


@register.simple_tag
def tapir_button_action():
    return "btn tapir-btn btn-primary"


@register.simple_tag
def tapir_button_custom(bootstrap_color):
    return f"btn tapir-btn btn-{bootstrap_color}"


@register.simple_tag
def feature_flag_enabled(flag_name: str):
    return FeatureFlag.get_flag_value(flag_name)


@register.inclusion_tag("core/tags/financing_campaign_progress_bar.html")
def campaign_progress_bar():
    campaign = FinancingCampaign.objects.order_by("-start_date").first()
    if not campaign:
        return

    return {
        "campaign": campaign,
        "progress": round(campaign.get_current_sum() * 100 / campaign.goal),
        "current_sum": round(campaign.get_current_sum()),
    }

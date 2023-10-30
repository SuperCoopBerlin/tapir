from django import template

from tapir.coop.models import (
    ShareOwner,
    MemberStatus,
    get_member_status_translation,
)

register = template.Library()


@register.inclusion_tag(
    "coop/tags/user_coop_share_ownership_list_tag.html", takes_context=True
)
def share_owner_ownership_list(context, share_owner: ShareOwner):
    context["share_owner"] = share_owner
    return context


@register.inclusion_tag("coop/tags/member_status_colored_text_tag.html")
def member_status_colored_text(share_owner: ShareOwner):
    status = share_owner.get_member_status()
    return {
        "text": get_member_status_translation(status),
        "color": MemberStatus.get_status_color(status),
    }

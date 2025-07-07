import datetime

from django import template
from django.conf import settings

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
    context["shifts_only"] = settings.SHIFTS_ONLY
    return context


@register.inclusion_tag("coop/tags/member_status_colored_text_tag.html")
def member_status_colored_text(
    share_owner: ShareOwner, at_datetime: datetime.datetime | datetime.date = None
):
    status = share_owner.get_member_status(at_datetime)
    return {
        "text": get_member_status_translation(status),
        "color": MemberStatus.get_status_color(status),
    }

from django import template

from tapir.accounts.models import TapirUser
from tapir.coop.models import (
    ShareOwner,
    MemberStatus,
)

register = template.Library()


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def share_owner_ownership_list(context, share_owner: ShareOwner):
    context["share_owner"] = share_owner
    return context


@register.inclusion_tag("coop/active_members_progress_bar.html", takes_context=True)
def active_members_progress_bar(context):
    active_members = ShareOwner.objects.with_status(MemberStatus.ACTIVE)

    context["active_members_with_account_count"] = TapirUser.objects.filter(
        share_owner__in=active_members
    ).count()
    context["target_member_count"] = 1000
    context["progress"] = round(
        100
        * context["active_members_with_account_count"]
        / context["target_member_count"]
    )
    return context

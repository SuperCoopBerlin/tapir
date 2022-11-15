import datetime

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
    total_active_members = ShareOwner.objects.with_status(MemberStatus.ACTIVE)
    active_members_on_start_date = ShareOwner.objects.with_status(
        MemberStatus.ACTIVE, datetime.date(year=2012, month=11, day=15)
    )

    member_count_on_start_date = TapirUser.objects.filter(
        share_owner__in=active_members_on_start_date
    ).count()
    context["member_count_on_start_date"] = member_count_on_start_date

    new_member_count_since_start_date = (
        TapirUser.objects.filter(share_owner__in=total_active_members).count()
        - member_count_on_start_date
    )
    context["new_member_count_since_start_date"] = new_member_count_since_start_date

    target_member_count = 1000
    context["target_member_count"] = target_member_count
    context["progress_on_start_date"] = round(
        100 * member_count_on_start_date / target_member_count
    )
    context["progress_since_start_date"] = round(
        100 * new_member_count_since_start_date / target_member_count
    )
    return context

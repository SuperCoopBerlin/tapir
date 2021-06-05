from django import template

from tapir.coop.models import ShareOwner

register = template.Library()


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def user_coop_share_ownership_list(context, user):
    context["user"] = user
    if hasattr(user, "share_owner"):
        context["owner"] = user.share_owner
    return context


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def share_owner_ownership_list(context, share_owner: ShareOwner):
    context["owner"] = share_owner
    return context

from django import template

from tapir.coop.models import ShareOwner

register = template.Library()


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def user_coop_share_ownership_list(context, user):
    context["user"] = user
    if hasattr(user, "coop_share_owner"):
        context["coop_share_owner"] = user.coop_share_owner
        context["coop_share_ownerships"] = user.coop_share_owner.share_ownerships.all()
    else:
        context["coop_share_ownerships"] = []
    return context


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def share_owner_ownership_list(context, share_owner: ShareOwner):
    context["coop_share_owner"] = share_owner
    context["coop_share_ownerships"] = share_owner.share_ownerships.all()
    return context

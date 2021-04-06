from django import template

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

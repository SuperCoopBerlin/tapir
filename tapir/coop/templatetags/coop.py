from django import template

register = template.Library()


@register.inclusion_tag(
    "coop/user_coop_share_ownership_list_tag.html", takes_context=True
)
def user_coop_share_ownership_list(context, user):
    context["user"] = user
    context["coop_share_ownerships"] = user.coop_share_ownerships.all()
    return context

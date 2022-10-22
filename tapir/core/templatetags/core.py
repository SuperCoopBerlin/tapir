from django import template
from django.contrib.auth.models import User

from tapir.core.config import TAPIR_TABLE_CLASSES, sidebar_link_groups
from tapir.core.models import SidebarLink

register = template.Library()


@register.inclusion_tag("core/sidebar_links.html", takes_context=True)
def sidebar_links(context):
    # TODO move to SidebarLinkGroups
    visible_groups = {}
    for group_name, group_links in sidebar_link_groups.groups.items():
        visible_links = [
            link for link in group_links if is_link_shown(context["request"].user, link)
        ]
        if len(visible_links) > 0:
            visible_groups[group_name] = visible_links

    for visible_links in visible_groups.values():
        for link in visible_links:
            link.is_active = link.url == context["request"].path

    # TODO : ordering of groups, ordering of links
    context["sidebar_link_groups"] = visible_groups

    return context


def is_link_shown(user: User, link: SidebarLink):
    # TODO : optimize by caching the permissions
    for permission in link.required_permissions:
        if not user.has_perm(permission):
            return False
    return True


@register.simple_tag
def tapir_table_classes():
    return TAPIR_TABLE_CLASSES

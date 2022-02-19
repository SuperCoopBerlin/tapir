from django import template

from tapir.core.config import sidebar_links_providers

register = template.Library()


@register.inclusion_tag("core/sidebar_links.html", takes_context=True)
def sidebar_links(context):
    link_groups = dict()

    for provider in sidebar_links_providers:
        provided_groups = provider(context["request"])
        if provided_groups is None:
            continue

        for group in provided_groups:
            if group.name in link_groups:
                link_groups[group.name].links += group.links
            else:
                link_groups[group.name] = group

    for empty_group in [
        group_name for group_name, group in link_groups.items() if len(group.links) == 0
    ]:
        del link_groups[empty_group]

    for group in link_groups.values():
        for link in group.links:
            link.is_active = link.url == context["request"].path

    link_groups = list(link_groups.values())
    link_groups.sort(key=lambda x: x.ordering)

    context["sidebar_link_groups"] = link_groups

    return context

from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_links_providers
from tapir.core.models import SidebarLink, SidebarLinkGroup


def get_sidebar_link_groups(request):
    links = [
        SidebarLink(
            display_name=_("Wiki"),
            material_icon="feed",
            url="https://wiki.supercoop.de",
        ),
        SidebarLink(
            display_name=_("Member manual"),
            material_icon="menu_book",
            url="https://wiki.supercoop.de/wiki/Member_Manual",
        ),
        SidebarLink(
            display_name=_("Shop opening hours"),
            material_icon="access_time",
            url="https://wiki.supercoop.de/wiki/%C3%96ffnungszeiten",
        ),
        SidebarLink(
            display_name=_("Contact the member office"),
            material_icon="email",
            url="mailto:mitglied@supercoop.de",
        ),
    ]

    return [
        SidebarLinkGroup(
            name=_("Miscellaneous"),
            ordering=1000,
            links=links,
        )
    ]


sidebar_links_providers.append(get_sidebar_link_groups)

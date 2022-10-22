from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_COOP_MANAGE


class CoreConfig(AppConfig):
    name = "tapir.core"

    def ready(self):
        self.register_sidebar_link_groups()

    @staticmethod
    def register_sidebar_link_groups():
        sidebar_link_groups.get_group(_("Management"), 2).add_link(
            display_name=_("Emails"),
            material_icon="mail",
            url=reverse_lazy("core:email_list"),
            ordering=2,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        misc_group = sidebar_link_groups.get_group(_("Miscellaneous"), 5)

        misc_group.add_link(
            display_name=_("Wiki"),
            material_icon="feed",
            url="https://wiki.supercoop.de",
            ordering=1,
        )

        misc_group.add_link(
            display_name=_("Member manual"),
            material_icon="menu_book",
            url="https://wiki.supercoop.de/wiki/Member_Manual",
            ordering=2,
        )

        misc_group.add_link(
            display_name=_("Shop opening hours"),
            material_icon="access_time",
            url="https://wiki.supercoop.de/wiki/%C3%96ffnungszeiten",
            ordering=3,
        )

        misc_group.add_link(
            display_name=_("Contact the member office"),
            material_icon="email",
            url="mailto:mitglied@supercoop.de",
            ordering=4,
        )

        misc_group.add_link(
            display_name=_("About tapir"),
            material_icon="help",
            url=reverse_lazy("coop:about"),
            ordering=7,
        )

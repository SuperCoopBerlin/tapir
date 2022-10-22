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
        group_name = _("Cooperative")

        sidebar_link_groups.add_link(
            group_name=group_name,
            display_name=_("Emails"),
            material_icon="mail",
            url=reverse_lazy("core:email_list"),
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        misc_group_name = _("Miscellaneous")

        sidebar_link_groups.add_link(
            group_name=misc_group_name,
            display_name=_("Wiki"),
            material_icon="feed",
            url="https://wiki.supercoop.de",
        )

        sidebar_link_groups.add_link(
            group_name=misc_group_name,
            display_name=_("Member manual"),
            material_icon="menu_book",
            url="https://wiki.supercoop.de/wiki/Member_Manual",
        )

        sidebar_link_groups.add_link(
            group_name=misc_group_name,
            display_name=_("Shop opening hours"),
            material_icon="access_time",
            url="https://wiki.supercoop.de/wiki/%C3%96ffnungszeiten",
        )

        sidebar_link_groups.add_link(
            group_name=misc_group_name,
            display_name=_("Contact the member office"),
            material_icon="email",
            url="mailto:mitglied@supercoop.de",
        )

        sidebar_link_groups.add_link(
            group_name=misc_group_name,
            display_name=_("About tapir"),
            material_icon="help",
            url=reverse_lazy("coop:about"),
        )

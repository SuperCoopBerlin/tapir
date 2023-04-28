from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_COOP_ADMIN


class AccountsConfig(AppConfig):
    name = "tapir.accounts"

    def ready(self):
        self.register_sidebar_link_groups()

    @staticmethod
    def register_sidebar_link_groups():
        sidebar_link_groups.get_group(_("Members"), 1).add_link(
            display_name=_("Groups"),
            material_icon="badge",
            url=reverse_lazy("accounts:ldap_group_list"),
            ordering=4,
            required_permissions=[PERMISSION_COOP_ADMIN],
        )

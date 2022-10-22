from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_COOP_MANAGE


class LogConfig(AppConfig):
    name = "tapir.log"

    def ready(self):
        self.register_sidebar_link_groups()

    @staticmethod
    def register_sidebar_link_groups():
        sidebar_link_groups.add_link(
            group_name=_("Cooperative"),
            display_name=_("Logs"),
            material_icon="manage_search",
            url=reverse_lazy("log:log_overview"),
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

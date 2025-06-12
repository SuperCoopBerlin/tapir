from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_WELCOMEDESK_VIEW


class WelcomedeskConfig(AppConfig):
    name = "tapir.welcomedesk"

    def ready(self):
        self.register_sidebar_link_groups()

    @staticmethod
    def register_sidebar_link_groups():
        if settings.SHIFTS_ONLY:
            return

        welcomedesk_group = sidebar_link_groups.get_group(_("Welcome Desk"), 3)

        welcomedesk_group.add_link(
            display_name=_("Welcome Desk"),
            material_icon="table_restaurant",
            url=reverse_lazy("welcomedesk:welcome_desk_search"),
            ordering=1,
            required_permissions=[PERMISSION_WELCOMEDESK_VIEW],
            html_id="welcome_desk_link",
        )

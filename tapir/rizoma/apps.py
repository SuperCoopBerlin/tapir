from django.apps import AppConfig
from tapir.core.config import sidebar_link_groups
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from tapir.settings import PERMISSION_COOP_ADMIN

class RizomaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tapir.rizoma"

    def ready(self):
        super().ready()
        self.register_rizoma_sidebar_link_groups()

    # Define custom links in the rizoma sidebar
    def register_rizoma_sidebar_link_groups(self):
        admin_group = sidebar_link_groups.get_group(_("Admin"), 0)

        admin_group.add_link(
            display_name=_("All shifts"),
            material_icon="calendar_today",
            url=reverse_lazy("rizoma:all_shifts"),
            ordering=1,
            required_permissions=[PERMISSION_COOP_ADMIN],
        )
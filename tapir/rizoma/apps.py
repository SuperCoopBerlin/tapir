from django.apps import AppConfig
from tapir.core.config import sidebar_link_groups
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from tapir.settings import PERMISSION_COOP_ADMIN, PERMISSION_COOP_VIEW

class RizomaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tapir.rizoma"

    def ready(self):
        super().ready()
        self.register_rizoma_sidebar_link_groups()

    # Define custom links in the rizoma sidebar
    def register_rizoma_sidebar_link_groups(self):
        turnos_group = sidebar_link_groups.get_group(_("Shifts"), 4)

        turnos_group.add_link(
            display_name=_("My shifts"),
            material_icon="calendar_today",
            url=reverse_lazy("shifts:dashboard"),
            ordering=0,
            # required_permissions=[PERMISSION_COOP_VIEW],
        )

        turnos_group.add_link(
            display_name=_("All shifts"),
            material_icon="calendar_today",
            url=reverse_lazy("rizoma:all_shifts"),
            ordering=0,
            # required_permissions=[PERMISSION_COOP_VIEW],
        )

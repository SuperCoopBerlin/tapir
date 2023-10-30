from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tapir.statistics"

    def ready(self):
        super().ready()

        misc_group = sidebar_link_groups.get_group(_("Miscellaneous"), 5)

        misc_group.add_link(
            display_name=_("Statistics"),
            material_icon="calculate",
            url=reverse("statistics:main_statistics"),
            ordering=1,
        )

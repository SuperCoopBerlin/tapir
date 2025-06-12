from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.core.config import sidebar_link_groups


class FinancingcampaignConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tapir.financingcampaign"

    def ready(self):
        if settings.SHIFTS_ONLY:
            return

        management_group = sidebar_link_groups.get_group(_("Management"), 2)
        management_group.add_link(
            display_name=_("Financing campaigns"),
            material_icon="euro",
            url=reverse_lazy("financingcampaign:general"),
            ordering=6,
            required_permissions=[settings.PERMISSION_COOP_ADMIN],
        )

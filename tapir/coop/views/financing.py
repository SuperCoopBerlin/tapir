from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from tapir.coop.forms import FinancingCampaignForm
from tapir.coop.models import (
    FinancingCampaign,
)
from tapir.core.config import sidebar_links_providers
from tapir.core.models import SidebarLink, SidebarLinkGroup


class FinancingCampaignUpdateView(PermissionRequiredMixin, generic.UpdateView):
    permission_required = "coop.manage"
    model = FinancingCampaign
    form_class = FinancingCampaignForm

    def get_success_url(self):
        return reverse("coop:financing_campaign_update", args=[self.object.pk])


def get_sidebar_link_groups(request):
    if not request.user.has_perm("coop.manage"):
        return None

    links = []
    for campaign in FinancingCampaign.objects.all():
        links.append(
            SidebarLink(
                display_name=_(campaign.name),
                material_icon="euro",
                url=campaign.get_absolute_url(),
            ),
        )

    return [
        SidebarLinkGroup(
            name=_("Financing campaign"),
            ordering=900,
            links=links,
        )
    ]


sidebar_links_providers.append(get_sidebar_link_groups)

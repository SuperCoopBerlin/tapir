from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views import generic

from tapir.coop.forms import FinancingCampaignForm
from tapir.coop.models import (
    FinancingCampaign,
)
from tapir.settings import PERMISSION_COOP_MANAGE


class FinancingCampaignUpdateView(PermissionRequiredMixin, generic.UpdateView):
    permission_required = PERMISSION_COOP_MANAGE
    model = FinancingCampaign
    form_class = FinancingCampaignForm

    def get_success_url(self):
        return reverse("coop:financing_campaign_update", args=[self.object.pk])

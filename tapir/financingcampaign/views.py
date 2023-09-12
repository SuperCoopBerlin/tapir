from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from tapir import settings
from tapir.core.views import TapirFormMixin
from tapir.financingcampaign.forms import (
    FinancingCampaignForm,
    FinancingSourceForm,
    FinancingSourceDatapointForm,
)
from tapir.financingcampaign.models import (
    FinancingCampaign,
    FinancingSource,
    FinancingSourceDatapoint,
)


class FinancingCampaignGeneralView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    permission_required = [settings.PERMISSION_COOP_ADMIN]
    template_name = "financingcampaign/general.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        context_data["campaigns"] = FinancingCampaign.objects.all().order_by(
            "-start_date"
        )
        context_data["sources"] = FinancingSource.objects.all().order_by(
            "campaign__start_date", "name"
        )
        context_data["datapoints"] = FinancingSourceDatapoint.objects.all().order_by(
            "-date"
        )
        return context_data


class FinancingCampaignBaseViewMixin(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin
):
    permission_required = [settings.PERMISSION_COOP_ADMIN]

    def get_success_url(self):
        return reverse("financingcampaign:general")


class FinancingCampaignDeleteBaseView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView
):
    permission_required = [settings.PERMISSION_COOP_ADMIN]
    template_name = "financingcampaign/confirm_delete.html"

    def get_success_url(self):
        return reverse("financingcampaign:general")


class FinancingCampaignCreateView(FinancingCampaignBaseViewMixin, generic.CreateView):
    model = FinancingCampaign
    form_class = FinancingCampaignForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Create a new financing campaign")
        context_data["card_title"] = context_data["page_title"]
        return context_data


class FinancingCampaignEditView(FinancingCampaignBaseViewMixin, generic.UpdateView):
    model = FinancingCampaign
    form_class = FinancingCampaignForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Edit financing campaign: %(name)s") % {
            "name": self.object.name
        }
        context_data["card_title"] = context_data["page_title"]
        return context_data


class FinancingCampaignDeleteView(FinancingCampaignDeleteBaseView):
    model = FinancingCampaign


class FinancingSourceCreateView(FinancingCampaignBaseViewMixin, generic.CreateView):
    model = FinancingSource
    form_class = FinancingSourceForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Create a new financing source")
        context_data["card_title"] = context_data["page_title"]
        return context_data


class FinancingSourceEditView(FinancingCampaignBaseViewMixin, generic.UpdateView):
    model = FinancingSource
    form_class = FinancingSourceForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Edit financing source: %(name)s") % {
            "name": self.object.name
        }
        context_data["card_title"] = context_data["page_title"]
        return context_data


class FinancingSourceDeleteView(FinancingCampaignDeleteBaseView):
    model = FinancingSource


class FinancingSourceDatapointCreateView(
    FinancingCampaignBaseViewMixin, generic.CreateView
):
    model = FinancingSourceDatapoint
    form_class = FinancingSourceDatapointForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Create a new financing source datapoint")
        context_data["card_title"] = context_data["page_title"]
        return context_data


class FinancingSourceDatapointEditView(
    FinancingCampaignBaseViewMixin, generic.UpdateView
):
    model = FinancingSourceDatapoint
    form_class = FinancingSourceDatapointForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Edit financing source datapoint: %(name)s") % {
            "name": self.object.name
        }
        context_data["card_title"] = context_data["page_title"]
        return context_data


class FinancingSourceDatapointDeleteView(FinancingCampaignDeleteBaseView):
    model = FinancingSourceDatapoint

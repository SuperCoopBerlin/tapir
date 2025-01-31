from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import generic

from tapir.settings import PERMISSION_COOP_MANAGE


class FancyGraphView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    permission_required = PERMISSION_COOP_MANAGE
    template_name = "statistics/fancy_graph.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data

import os

from django.views import generic


class AboutView(generic.TemplateView):
    template_name = "coop/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tapir_version"] = os.getenv("TAPIR_VERSION")
        return context

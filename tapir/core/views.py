from django.views.generic import TemplateView

from tapir.core.tapir_email_base import all_emails


class EmailListView(TemplateView):
    template_name = "core/email_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emails_for_template = []
        for email in all_emails.values():
            email_for_template = {
                "code": email.get_unique_id(),
                "name": email.get_name(),
                "description": email.get_description(),
            }
            emails_for_template.append(email_for_template)
        context["emails"] = emails_for_template
        return context

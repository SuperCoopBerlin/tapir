from django.urls import reverse
from django.views.generic import TemplateView

from tapir.core.tapir_email_base import all_emails
from tapir.log.models import EmailLogEntry


class EmailListView(TemplateView):
    template_name = "core/email_list.html"

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        emails_for_template = []
        for index, email in enumerate(all_emails.values()):
            dummy = email.get_dummy_version()

            example = (
                EmailLogEntry.objects.filter(email_id=email.get_unique_id())
                .order_by("?")
                .first()
            )
            if example is not None:
                example = reverse("log:email_log_entry_content", args=[example.id])

            email_for_template = {
                "code": email.get_unique_id(),
                "name": email.get_name(),
                "description": email.get_description(),
                "subject": dummy.get_subject(dummy.context),
                "body": dummy.get_body(dummy.context),
                "example": example,
                "html_id": f"email_{index}",
            }
            emails_for_template.append(email_for_template)

        view_context["emails"] = emails_for_template
        return view_context

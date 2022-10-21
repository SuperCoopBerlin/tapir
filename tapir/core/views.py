from typing import Type

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from tapir.core.tapir_email_base import all_emails, TapirEmailBase
from tapir.log.models import EmailLogEntry
from tapir.settings import PERMISSION_COOP_MANAGE


class EmailListView(PermissionRequiredMixin, TemplateView):
    template_name = "core/email_list.html"

    permission_required = PERMISSION_COOP_MANAGE

    def get_context_data(self, **kwargs):
        language = self.request.user.preferred_language
        if "force_language" in self.request.GET.keys():
            language = self.request.GET["force_language"]

        view_context = super().get_context_data(**kwargs)
        emails_for_template = []
        for index, email in enumerate(all_emails.values()):
            email: Type[TapirEmailBase]
            dummy = email.get_dummy_version()

            example = (
                EmailLogEntry.objects.filter(email_id=email.get_unique_id())
                .order_by("created_date")
                .last()
            )
            if example is not None:
                example = reverse("log:email_log_entry_content", args=[example.id])

            with translation.override(language):
                subject = (
                    dummy.get_subject(dummy.context) if dummy else _("Not available")
                )
                body = dummy.get_body(dummy.context) if dummy else _("Not available")

            email_for_template = {
                "code": email.get_unique_id(),
                "name": email.get_name(),
                "description": email.get_description(),
                "subject": subject,
                "body": body,
                "example": example,
                "html_id": f"email_{index}",
            }
            emails_for_template.append(email_for_template)

        view_context["emails"] = emails_for_template
        return view_context

from typing import Type

from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, ListView, UpdateView

from tapir.core.models import FeatureFlag
from tapir.core.tapir_email_base import all_emails, TapirEmailBase
from tapir.log.models import EmailLogEntry
from tapir.settings import PERMISSION_COOP_MANAGE, PERMISSION_COOP_ADMIN


class TapirFormMixin:
    @staticmethod
    def get_template_names():
        return ["core/tapir_form.html", "core/tapir_form.default.html"]


class EmailListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
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


class FeatureFlagListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "core/featureflag_list.html"
    model = FeatureFlag
    permission_required = PERMISSION_COOP_ADMIN


class FeatureFlagUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, UpdateView
):
    model = FeatureFlag
    fields = ["flag_value"]
    permission_required = [PERMISSION_COOP_ADMIN]

    def get_success_url(self):
        return reverse("core:featureflag_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature_flag: FeatureFlag = self.object
        context["page_title"] = _("Feature: %(name)s") % {
            "name": feature_flag.flag_name
        }
        context["card_title"] = context["page_title"]
        return context

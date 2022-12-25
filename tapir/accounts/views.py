import django.contrib.auth.views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from tapir.accounts.forms import TapirUserForm, PasswordResetForm
from tapir.accounts.models import TapirUser, UpdateTapirUserLogEntry
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import PERMISSION_ACCOUNTS_MANAGE


class TapirUserDetailView(PermissionRequiredMixin, generic.DetailView):
    model = TapirUser
    template_name = "accounts/user_detail.html"

    def get_permission_required(self):
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return [PERMISSION_ACCOUNTS_MANAGE]


class TapirUserMeView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("accounts:user_detail", args=[self.request.user.pk])


class TapirUserUpdateView(
    PermissionRequiredMixin, UpdateViewLogMixin, TapirFormMixin, generic.UpdateView
):
    permission_required = PERMISSION_ACCOUNTS_MANAGE
    model = TapirUser
    form_class = TapirUserForm

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                UpdateTapirUserLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    tapir_user=form.instance,
                    actor=self.request.user,
                ).save()

            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        tapir_user: TapirUser = self.object
        context["page_title"] = _("Edit member: %(name)s") % {
            "name": tapir_user.get_display_name()
        }
        context["card_title"] = _("Edit member: %(name)s") % {
            "name": tapir_user.get_html_link()
        }
        return context


class PasswordResetView(auth_views.PasswordResetView):
    # Form class to allow password reset despite unusable password in the db
    form_class = PasswordResetForm


@require_POST
@csrf_protect
@permission_required(PERMISSION_ACCOUNTS_MANAGE)
def send_user_welcome_email(request, pk):
    tapir_user = get_object_or_404(TapirUser, pk=pk)

    email = TapirAccountCreatedEmail(tapir_user)
    email.send_to_tapir_user(actor=request.user, recipient=tapir_user)

    messages.info(request, _("Account welcome email sent."))

    return redirect(tapir_user.get_absolute_url())


class UpdatePurchaseTrackingAllowedView(PermissionRequiredMixin, generic.RedirectView):
    def has_permission(self):
        return self.request.user and self.request.user.pk == self.kwargs["pk"]

    def get_redirect_url(self, *args, **kwargs):
        return get_object_or_404(TapirUser, pk=self.kwargs["pk"]).get_absolute_url()

    def get(self, request, *args, **kwargs):
        tapir_user = get_object_or_404(TapirUser, pk=self.kwargs["pk"])

        old_frozen = freeze_for_log(tapir_user)
        tapir_user.allows_purchase_tracking = kwargs["allowed"] > 0
        new_frozen = freeze_for_log(tapir_user)

        with transaction.atomic():
            if old_frozen != new_frozen:
                UpdateTapirUserLogEntry().populate(
                    old_frozen=old_frozen,
                    new_frozen=new_frozen,
                    tapir_user=tapir_user,
                    actor=request.user,
                ).save()

            tapir_user.save()

        return super().get(request, args, kwargs)

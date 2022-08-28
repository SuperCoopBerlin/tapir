import django.contrib.auth.views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from tapir import settings
from tapir.accounts.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.accounts.forms import TapirUserForm, PasswordResetForm
from tapir.accounts.models import TapirUser, UpdateTapirUserLogEntry
from tapir.log.models import EmailLogEntry
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.utils.email_utils import EmailUtils


class UserDetailView(PermissionRequiredMixin, generic.DetailView):
    model = TapirUser
    template_name = "accounts/user_detail.html"

    def get_permission_required(self):
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return ["accounts.manage"]


class UserMeView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("accounts:user_detail", args=[self.request.user.pk])


class UserUpdateView(PermissionRequiredMixin, UpdateViewLogMixin, generic.UpdateView):
    permission_required = "accounts.manage"
    model = TapirUser
    form_class = TapirUserForm
    template_name = "accounts/user_form.html"

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                log_entry = UpdateTapirUserLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    user=form.instance,
                    actor=self.request.user,
                )
                log_entry.save()

            return response


class PasswordResetView(auth_views.PasswordResetView):
    # Form class to allow password reset despite unusable password in the db
    form_class = PasswordResetForm


@require_POST
@csrf_protect
@permission_required("accounts.manage")
def send_user_welcome_email(request, pk):
    tapir_user = get_object_or_404(TapirUser, pk=pk)

    email = TapirAccountCreatedEmail(tapir_user)
    email.send_to_tapir_user(actor=request.user, recipient=tapir_user)

    messages.info(request, _("Account welcome email sent."))

    return redirect(tapir_user.get_absolute_url())

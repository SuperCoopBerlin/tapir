import django.contrib.auth.views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from tapir.accounts.forms import TapirUserForm, PasswordResetForm
from tapir.accounts.models import TapirUser


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


class UserUpdateView(PermissionRequiredMixin, generic.UpdateView):
    permission_required = "accounts.manage"
    model = TapirUser
    form_class = TapirUserForm
    template_name = "accounts/user_form.html"


class PasswordResetView(auth_views.PasswordResetView):
    # Form class to allow password reset despite unusable password in the db
    form_class = PasswordResetForm


@require_POST
@csrf_protect
@permission_required("accounts.manage")
def send_user_welcome_email(request, pk):
    u = get_object_or_404(TapirUser, pk=pk)
    u.send_welcome_email()
    messages.info(request, _("Welcome email sent."))

    return redirect(u.get_absolute_url())

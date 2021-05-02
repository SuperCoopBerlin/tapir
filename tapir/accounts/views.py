import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import django.contrib.auth.views as auth_views
from django.urls import reverse, reverse_lazy
from django.views import generic

from tapir.accounts.forms import UserForm, PasswordResetForm
from tapir.accounts.models import TapirUser
from tapir.shifts.models import ShiftAttendance, ShiftAttendanceTemplate


class UserDetailView(PermissionRequiredMixin, generic.DetailView):
    model = TapirUser
    context_object_name = "user"
    template_name = "accounts/user_detail.html"
    permission_required = "accounts.manage"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        max_date = datetime.datetime.now() + datetime.timedelta(days=90)
        user: TapirUser = context_data["user"]
        context_data["shift_attendances"] = ShiftAttendance.objects.filter(
            user=user,
            state=ShiftAttendance.State.PENDING,
            shift__start_time__lt=max_date,
        ).order_by("shift__start_time")
        context_data[
            "shift_template_attendances"
        ] = ShiftAttendanceTemplate.objects.filter(user=user)
        return context_data


class UserMeView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("accounts:user_detail", args=[self.request.user.pk])


class UserUpdateView(PermissionRequiredMixin, generic.UpdateView):
    permission_required = "accounts.manage"
    model = TapirUser
    form_class = UserForm
    template_name = "accounts/user_form.html"


class PasswordResetView(auth_views.PasswordResetView):
    # Form class to allow password reset despite unusable password in the db
    form_class = PasswordResetForm

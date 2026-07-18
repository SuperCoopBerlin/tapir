from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from tapir.coop.forms import CoopAddressForm
from tapir.coop.models import CoopAddress
from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_COOP_ADMIN


class CoopManagementView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    UpdateView,
):
    model = CoopAddress
    form_class = CoopAddressForm
    success_url = reverse_lazy("accounts:user_me")
    permission_required = PERMISSION_COOP_ADMIN

    def get_object(self, queryset=None):
        obj, created = CoopAddress.objects.get_or_create(pk=1)
        return obj

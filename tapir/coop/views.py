from datetime import date

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic import UpdateView, CreateView

from tapir.accounts.models import TapirUser
from tapir.coop.forms import CoopShareOwnershipForm
from tapir.coop.models import CoopShareOwnership, DraftUser


class CoopShareOwnershipViewMixin(PermissionRequiredMixin):
    permission_required = "coop.manage"
    model = CoopShareOwnership
    form_class = CoopShareOwnershipForm

    def get_success_url(self):
        # After successful creation or update of a CoopShareOwnership, return to the user overview page.
        return reverse("accounts:user_detail", args=[self.object.user.pk])


class CoopShareOwnershipUpdateView(CoopShareOwnershipViewMixin, UpdateView):
    pass


class CoopShareOwnershipCreateView(CoopShareOwnershipViewMixin, CreateView):
    def get_initial(self):
        return {"start_date": date.today()}

    def get_form_kwargs(self):
        user = get_object_or_404(TapirUser, pk=self.kwargs["user_pk"])
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = CoopShareOwnership(user=user)
        return kwargs


class DraftUserViewMixin(PermissionRequiredMixin):
    success_url = reverse_lazy("accounts:draftuser_list")
    permission_required = "coop.manage"
    model = DraftUser
    fields = [
        "first_name",
        "last_name",
        "username",
        "email",
        "num_shares",
        "attended_welcome_session",
    ]


class DraftUserListView(DraftUserViewMixin, generic.ListView):
    pass


class DraftUserCreateView(DraftUserViewMixin, generic.CreateView):
    pass


class DraftUserUpdateView(DraftUserViewMixin, generic.UpdateView):
    pass


class DraftUserDetailView(DraftUserViewMixin, generic.UpdateView):
    pass


class DraftUserDeleteView(DraftUserViewMixin, generic.DeleteView):
    pass

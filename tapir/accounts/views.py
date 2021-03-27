from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views import generic

from tapir.accounts.models import DraftUser, TapirUser


class UserDetailView(generic.DetailView):
    model = TapirUser
    context_object_name = "user"
    template_name = "accounts/user_detail.html"


class UserMeView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("accounts:user_detail", args=[self.request.user.pk])


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


class DraftUserDeleteView(DraftUserViewMixin, generic.DeleteView):
    pass

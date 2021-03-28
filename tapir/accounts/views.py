from django.urls import reverse
from django.views import generic

from tapir.accounts.models import TapirUser


class UserDetailView(generic.DetailView):
    model = TapirUser
    context_object_name = "user"
    template_name = "accounts/user_detail.html"


class UserMeView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("accounts:user_detail", args=[self.request.user.pk])

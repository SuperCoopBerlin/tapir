from datetime import date

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
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


class DraftUserDetailView(DraftUserViewMixin, generic.DetailView):
    pass


class DraftUserDeleteView(DraftUserViewMixin, generic.DeleteView):
    pass


@require_POST
@csrf_protect
@permission_required("coop.manage")
def mark_signed_membership_agreement(request, pk):
    u = DraftUser.objects.get(pk=pk)
    u.signed_membership_agreement = True
    u.save()

    return redirect(u)


@require_POST
@csrf_protect
@permission_required("coop.manage")
def mark_attended_welcome_session(request, pk):
    u = DraftUser.objects.get(pk=pk)
    u.attended_welcome_session = True
    u.save()

    return redirect(u)


@require_POST
@csrf_protect
@permission_required("coop.manage")
def create_user_from_draftuser(request, pk):
    draft = DraftUser.objects.get(pk=pk)
    if not draft.signed_membership_agreement:
        # TODO(Leon Handreke): Error message
        return redirect(draft)

    with transaction.atomic():
        u = TapirUser.objects.create(
            username=draft.username,
            first_name=draft.first_name,
            last_name=draft.last_name,
            email=draft.email,
        )
        for _ in range(0, draft.num_shares):
            CoopShareOwnership.objects.create(
                user=u, start_date=date.today(),
            )
        draft.delete()

    # TODO(Leon Handreke): Why does just passing u here not work?
    return redirect(u.get_absolute_url())

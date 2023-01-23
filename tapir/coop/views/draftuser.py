from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.datetime_safe import date
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET

from tapir.coop import pdfs
from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.emails.membership_confirmation_email_for_active_member import (
    MembershipConfirmationForActiveMemberEmail,
)
from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
    MembershipConfirmationForInvestingMemberEmail,
)
from tapir.coop.forms import (
    DraftUserForm,
    DraftUserRegisterForm,
)
from tapir.coop.models import (
    DraftUser,
    ShareOwner,
    ShareOwnership,
    NewMembershipsForAccountingRecap,
)
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.utils.models import copy_user_info
from tapir.utils.shortcuts import set_header_for_file_download


class DraftUserListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = PERMISSION_COOP_MANAGE
    model = DraftUser
    ordering = ["created_at"]


class DraftUserCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, generic.CreateView
):
    permission_required = PERMISSION_COOP_MANAGE
    model = DraftUser
    form_class = DraftUserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["page_title"] = _("Create applicant")
        context["card_title"] = _("Create applicant")
        return context


class DraftUserRegisterView(generic.CreateView):
    model = DraftUser
    form_class = DraftUserRegisterForm
    success_url = reverse_lazy("coop:draftuser_confirm_registration")

    def get_template_names(self):
        return [
            "coop/draftuser_register_form.html",
            "coop/draftuser_register_form.default.html",
        ]


class DraftUserConfirmRegistrationView(generic.TemplateView):
    template_name = "coop/draftuser_confirm_registration.html"


class DraftUserUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, generic.UpdateView
):
    permission_required = PERMISSION_COOP_MANAGE
    model = DraftUser
    form_class = DraftUserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        draft_user: DraftUser = self.object
        context["page_title"] = _("Edit applicant: %(name)s") % {
            "name": draft_user.get_display_name()
        }
        context["card_title"] = _("Edit applicant: %(name)s") % {
            "name": draft_user.get_html_link()
        }
        return context


class DraftUserDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    permission_required = PERMISSION_COOP_MANAGE
    model = DraftUser


class DraftUserDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView
):
    permission_required = PERMISSION_COOP_MANAGE
    success_url = reverse_lazy("coop:draftuser_list")
    model = DraftUser


@require_GET
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def draftuser_membership_agreement(request, pk):
    draft_user = get_object_or_404(DraftUser, pk=pk)
    filename = "Beteiligungserklärung %s %s.pdf" % (
        draft_user.first_name,
        draft_user.last_name,
    )

    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)
    response.write(pdfs.get_membership_agreement_pdf(draft_user).write_pdf())
    return response


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def mark_signed_membership_agreement(request, pk):
    user = DraftUser.objects.get(pk=pk)
    user.signed_membership_agreement = True
    user.save()

    return redirect(user)


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def mark_attended_welcome_session(request, pk):
    user = DraftUser.objects.get(pk=pk)
    user.attended_welcome_session = True
    user.save()

    return redirect(user)


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def register_draftuser_payment(request, pk):
    draft = get_object_or_404(DraftUser, pk=pk)
    draft.paid_membership_fee = True
    draft.save()
    return redirect(draft.get_absolute_url())


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def create_share_owner_from_draft_user_view(request, pk):
    draft_user = DraftUser.objects.get(pk=pk)

    if not draft_user.can_create_user():
        raise ValidationError(
            "DraftUser is not ready (could be missing information or invalid amount of shares)"
        )

    with transaction.atomic():
        share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
        draft_user.delete()

        NewMembershipsForAccountingRecap.objects.create(
            member=share_owner,
            number_of_shares=share_owner.get_active_share_ownerships().count(),
            date=timezone.now().date(),
        )

        email = (
            MembershipConfirmationForInvestingMemberEmail
            if share_owner.is_investing
            else MembershipConfirmationForActiveMemberEmail
        )(share_owner=share_owner)
        email.send_to_share_owner(actor=request.user, recipient=share_owner)

    return redirect(share_owner.get_absolute_url())


def create_share_owner_and_shares_from_draft_user(draft_user: DraftUser) -> ShareOwner:
    share_owner = ShareOwner.objects.create(
        is_company=False,
        is_investing=draft_user.is_investing,
        ratenzahlung=draft_user.ratenzahlung,
        attended_welcome_session=draft_user.attended_welcome_session,
        paid_membership_fee=draft_user.paid_membership_fee,
    )

    copy_user_info(draft_user, share_owner)
    share_owner.save()

    for _ in range(0, draft_user.num_shares):
        ShareOwnership.objects.create(
            share_owner=share_owner,
            start_date=date.today(),
            amount_paid=(COOP_SHARE_PRICE if draft_user.paid_shares else 0),
        )

    return share_owner

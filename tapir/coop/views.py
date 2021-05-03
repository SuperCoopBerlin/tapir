from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import UpdateView, CreateView

from tapir.accounts.models import TapirUser
from tapir.coop import pdfs
from tapir.coop.forms import (
    CoopShareOwnershipForm,
    DraftUserForm,
    DraftUserRegisterForm,
)
from tapir.coop.models import ShareOwnership, DraftUser, ShareOwner
from tapir.utils.user_utils import UserUtils


class ShareOwnershipViewMixin:
    model = ShareOwnership
    form_class = CoopShareOwnershipForm

    def get_success_url(self):
        # After successful creation or update of a ShareOwnership, return to the user overview page.
        return self.object.owner.get_absolute_url()


class ShareOwnershipUpdateView(
    PermissionRequiredMixin, ShareOwnershipViewMixin, UpdateView
):
    permission_required = "coop.manage"


class ShareOwnershipCreateForUserView(
    PermissionRequiredMixin, ShareOwnershipViewMixin, CreateView
):
    permission_required = "coop.manage"

    def get_initial(self):
        return {"start_date": date.today(), "user": self._get_user()}

    def _get_user(self):
        return get_object_or_404(TapirUser, pk=self.kwargs["user_pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user"] = self._get_user()
        return ctx

    def form_valid(self, form):
        user = self._get_user()
        if hasattr(user, "coop_share_owner"):
            share_owner = user.coop_share_owner
        else:
            share_owner = ShareOwner.objects.create(user=user, is_company=False)
        form.instance.owner = share_owner
        return super().form_valid(form)


class DraftUserViewMixin:
    model = DraftUser
    form_class = DraftUserForm


class DraftUserListView(PermissionRequiredMixin, DraftUserViewMixin, generic.ListView):
    permission_required = "coop.manage"


class DraftUserCreateView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.CreateView
):
    permission_required = "coop.manage"
    template_name = "coop/draftuser_create_form.html"


class DraftUserRegisterView(DraftUserViewMixin, generic.CreateView):
    template_name = "coop/draftuser_register_form.html"
    form_class = DraftUserRegisterForm
    success_url = "/coop/user/draft/register/confirm"


class DraftUserConfirmRegistrationView(DraftUserViewMixin, generic.TemplateView):
    template_name = "coop/draftuser_confirm_registration.html"


class DraftUserUpdateView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.UpdateView
):
    permission_required = "coop.manage"


class DraftUserDetailView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.DetailView
):
    permission_required = "coop.manage"


class DraftUserDeleteView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.DeleteView
):
    pass


class ShareOwnerViewMixin:
    model = ShareOwner


class ShareOwnerDetailView(
    PermissionRequiredMixin, ShareOwnerViewMixin, generic.DetailView
):
    permission_required = "coop.manage"


@require_GET
@permission_required("coop.manage")
def draftuser_membership_agreement(request, pk):
    draft_user = get_object_or_404(DraftUser, pk=pk)
    filename = "Beteiligungserklärung %s %s.pdf" % (
        draft_user.first_name,
        draft_user.last_name,
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="{}"'.format(filename)
    response.write(pdfs.get_membership_agreement_pdf(draft_user).write_pdf())
    return response


@require_GET
@permission_required("coop.manage")
def empty_membership_agreement(request):
    filename = "Beteiligungserklärung SuperCoop eG.pdf"
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
    response.write(pdfs.get_membership_agreement_pdf().write_pdf())
    return response


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
            birthdate=draft.birthdate,
            street=draft.street,
            street_2=draft.street_2,
            postcode=draft.postcode,
            city=draft.city,
            country=draft.country,
        )
        if draft.num_shares > 0:
            share_owner = ShareOwner.objects.create(user=u, is_company=False)
            for _ in range(0, draft.num_shares):
                ShareOwnership.objects.create(
                    owner=share_owner,
                    start_date=date.today(),
                )
        if draft.odoo_partner:
            draft.odoo_partner.user = u
            draft.odoo_partner.save()

        if draft.coop_share_invoice:
            draft.coop_share_invoice.user = u
            draft.coop_share_invoice.save()

        draft.delete()

    return redirect(u.get_absolute_url())


@csrf_protect
@permission_required("coop.manage")
def create_user_from_shareowner(request, pk):
    shareowner = ShareOwner.objects.get(pk=pk)

    if shareowner.user is not None:
        raise Exception("This ShareOwner already has a User")

    if shareowner.is_company:
        raise Exception("This ShareOwner is a company")

    with transaction.atomic():
        user = TapirUser.objects.create(
            username=UserUtils.build_username(
                shareowner.first_name, shareowner.last_name
            ),
            first_name=shareowner.first_name,
            last_name=shareowner.last_name,
            email=shareowner.email,
            birthdate=shareowner.birthdate,
            street=shareowner.street,
            street_2=shareowner.street_2,
            postcode=shareowner.postcode,
            city=shareowner.city,
            country=shareowner.country,
        )
        shareowner.user = user
        shareowner.is_investing = False
        shareowner.save()
        user.save()

    return redirect(user.get_absolute_url())


@require_POST
@csrf_protect
@permission_required("coop.manage")
def create_share_owner_from_draftuser(request, pk):
    # This is intended for "Investing Members" : members that own a share but don't intend to participate actively
    # Therefore, compared to "create_user_from_draftuser", we create a ShareOwner object but no TapirUser

    draft = DraftUser.objects.get(pk=pk)
    if not draft.signed_membership_agreement:
        # TODO(Leon Handreke): Error message
        return redirect(draft)

    if draft.num_shares < 0:
        raise Exception(
            "Trying to create a share owner from a draft user without shares"
        )

    with transaction.atomic():
        share_owner = ShareOwner.objects.create(is_company=False)
        share_owner.user = None
        share_owner.company_name = ""
        share_owner.first_name = draft.first_name
        share_owner.last_name = draft.last_name
        share_owner.email = draft.email
        share_owner.birthdate = draft.birthdate
        share_owner.street = draft.street
        share_owner.street_2 = draft.street_2
        share_owner.postcode = draft.postcode
        share_owner.city = draft.city
        share_owner.country = draft.country
        share_owner.is_investing = True
        share_owner.save()

        for _ in range(0, draft.num_shares):
            ShareOwnership.objects.create(
                owner=share_owner,
                start_date=date.today(),
            )

        if draft.odoo_partner:
            draft.odoo_partner.save()

        if draft.coop_share_invoice:
            draft.coop_share_invoice.save()

        draft.delete()

    return redirect(share_owner.get_absolute_url())


# We're calling an already-protected view internally, but let's be sure nobody ever forgets.
@require_POST
@csrf_protect
@permission_required("coop.manage")
def register_draftuser_payment_cash(request, pk):
    return register_draftuser_payment(request, pk, settings.ODOO_JOURNAL_ID_CASH)


# We're calling an already-protected view internally, but let's be sure nobody ever forgets.
@require_POST
@csrf_protect
@permission_required("coop.manage")
def register_draftuser_payment_bank(request, pk):
    return register_draftuser_payment(request, pk, settings.ODOO_JOURNAL_ID_BANK)


@require_POST
@csrf_protect
@permission_required("coop.manage")
def register_draftuser_payment(request, pk, odoo_journal_id):
    draft = get_object_or_404(DraftUser, pk=pk)
    draft.create_coop_share_invoice()
    draft.coop_share_invoice.register_payment(
        draft.get_initial_amount(), odoo_journal_id
    )
    return redirect(draft.get_absolute_url())


@require_POST
@csrf_protect
@permission_required("coop.manage")
def send_shareowner_membership_confirmation_welcome_email(request, pk):
    owner = get_object_or_404(ShareOwner, pk=pk)
    mail = EmailMessage(
        subject=_("Willkommen bei SuperCoop eG!"),
        body=render_to_string(
            "coop/email/membership_confirmation_welcome.txt", {"owner": owner}
        ),
        from_email="mitglied@supercoop.de",
        to=[owner.get_email()],
        attachments=[
            (
                "Mitgliedschaftsbestätigung %s.pdf" % owner.get_display_name(),
                pdfs.get_shareowner_membership_confirmation_pdf(owner).write_pdf(),
                "application/pdf",
            )
        ],
    )
    mail.send()

    # TODO(Leon Handreke): Add a message to the user log here.
    messages.success(request, "Welcome email with Mitgliedschaftsbestätigung sent.")
    return redirect(owner.get_absolute_url())


@require_GET
@permission_required("coop.manage")
def shareowner_membership_confirmation(request, pk):
    owner = get_object_or_404(ShareOwner, pk=pk)
    filename = "Mitgliedschaftsbestätigung %s.pdf" % owner.get_display_name()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="{}"'.format(filename)
    response.write(pdfs.get_shareowner_membership_confirmation_pdf(owner).write_pdf())
    return response


class ActiveShareOwnerListView(PermissionRequiredMixin, generic.ListView):
    permission_required = "coop.manage"
    model = ShareOwner
    template_name = "coop/shareowner_list.html"

    def get_queryset(self):
        # TODO(Leon Handreke): Allow passing a date
        return ShareOwner.objects.filter(
            share_ownerships__in=ShareOwnership.objects.active_temporal()
        ).distinct()

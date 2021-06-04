import csv
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import UpdateView, CreateView

from tapir.accounts.models import TapirUser
from tapir.coop import pdfs
from tapir.coop.forms import (
    ShareOwnershipForm,
    DraftUserForm,
    DraftUserRegisterForm,
    ShareOwnerForm,
)
from tapir.coop.models import ShareOwnership, DraftUser, ShareOwner
from tapir.utils.user_utils import UserUtils


class ShareOwnershipViewMixin:
    model = ShareOwnership
    form_class = ShareOwnershipForm

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
    permission_required = "coop.manage"
    success_url = reverse_lazy("coop:draftuser_list")
    pass


class ShareOwnerViewMixin:
    model = ShareOwner


class ShareOwnerDetailView(
    PermissionRequiredMixin, ShareOwnerViewMixin, generic.DetailView
):
    permission_required = "coop.manage"


class ShareOwnerUpdateView(
    PermissionRequiredMixin, ShareOwnerViewMixin, generic.UpdateView
):
    permission_required = "accounts.manage"
    model = ShareOwner
    form_class = ShareOwnerForm


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
def mark_shareowner_attended_welcome_session(request, pk):
    u = ShareOwner.objects.get(pk=pk)
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
            share_owner = ShareOwner.objects.create(
                user=u,
                is_company=False,
                from_startnext=draft.from_startnext,
                ratenzahlung=draft.ratenzahlung,
                attended_welcome_session=draft.attended_welcome_session,
            )
            for _ in range(0, draft.num_shares):
                ShareOwnership.objects.create(
                    owner=share_owner,
                    start_date=date.today(),
                )
        draft.delete()

    return redirect(u.get_absolute_url())


class CreateUserFromShareOwnerView(PermissionRequiredMixin, generic.CreateView):
    model = TapirUser
    template_name = "coop/create_user_from_shareowner_form.html"
    permission_required = "coop.manage"
    fields = ["first_name", "last_name", "username"]

    def get_shareowner(self):
        return get_object_or_404(ShareOwner, pk=self.kwargs["shareowner_pk"])

    def dispatch(self, request, *args, **kwargs):
        owner = self.get_shareowner()
        # Not sure if 403 is the right error code here...
        if owner.user is not None:
            return HttpResponseForbidden("This ShareOwner already has a User")
        if owner.is_company:
            return HttpResponseForbidden("This ShareOwner is a company")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        owner = self.get_shareowner()
        user = TapirUser(
            first_name=owner.first_name,
            last_name=owner.last_name,
            email=owner.email,
            birthdate=owner.birthdate,
            street=owner.street,
            street_2=owner.street_2,
            postcode=owner.postcode,
            city=owner.city,
            country=owner.country,
        )
        kwargs.update({"instance": user})
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            owner = self.get_shareowner()
            owner.user = form.instance
            owner.blank_info_fields()
            owner.save()
            return response


@require_POST
@csrf_protect
@permission_required("coop.manage")
def create_share_owner_from_draftuser(request, pk):
    # For now, we don't create users for our new members yet but only ShareOwners. Later, this will be used for
    # investing members

    draft = DraftUser.objects.get(pk=pk)
    if not draft.signed_membership_agreement:
        # TODO(Leon Handreke): Error message
        return redirect(draft)

    if draft.num_shares < 0:
        raise Exception(
            "Trying to create a share owner from a draft user without shares"
        )

    with transaction.atomic():
        share_owner = ShareOwner.objects.create(
            is_company=False,
            first_name=draft.first_name,
            last_name=draft.last_name,
            email=draft.email,
            birthdate=draft.birthdate,
            street=draft.street,
            street_2=draft.street_2,
            postcode=draft.postcode,
            city=draft.city,
            country=draft.country,
            is_investing=draft.is_investing,
            from_startnext=draft.from_startnext,
            ratenzahlung=draft.ratenzahlung,
            attended_welcome_session=draft.attended_welcome_session,
        )

        for _ in range(0, draft.num_shares):
            ShareOwnership.objects.create(
                owner=share_owner,
                start_date=date.today(),
            )

        draft.delete()

    return redirect(share_owner.get_absolute_url())


@require_POST
@csrf_protect
@permission_required("coop.manage")
def register_draftuser_payment(request, pk):
    draft = get_object_or_404(DraftUser, pk=pk)
    draft.paid_membership_fee = True
    draft.save()
    return redirect(draft.get_absolute_url())


@require_POST
@csrf_protect
@permission_required("coop.manage")
def send_shareowner_membership_confirmation_welcome_email(request, pk):
    owner = get_object_or_404(ShareOwner, pk=pk)
    mail = EmailMessage(
        subject=_("Willkommen bei SuperCoop eG!"),
        body=render_to_string(
            "coop/email/membership_confirmation_welcome.html", {"owner": owner}
        ),
        from_email="SuperCoop Mitgliederbüro <mitglied@supercoop.de>",
        to=[owner.get_info().email],
        attachments=[
            (
                "Mitgliedschaftsbestätigung %s.pdf"
                % owner.get_info().get_display_name(),
                pdfs.get_shareowner_membership_confirmation_pdf(owner).write_pdf(),
                "application/pdf",
            )
        ],
    )
    mail.content_subtype = "html"
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


@require_GET
@permission_required("coop.manage")
def shareowner_membership_agreement(request, pk):
    owner = get_object_or_404(ShareOwner, pk=pk)
    filename = "Beteiligungserklärung %s.pdf" % owner.get_display_name()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="{}"'.format(filename)
    response.write(pdfs.get_membership_agreement_pdf(owner).write_pdf())
    return response


class ShareOwnerSearchMixin:
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.count() == 1:
            return HttpResponseRedirect(queryset.first().get_absolute_url())
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        searches = self.request.GET.get("search", "").split(" ")
        searches = [s for s in searches if s != ""]

        if len(searches) == 1 and searches[0].isdigit():
            queryset = queryset.filter(pk=int(searches[0]))
        elif searches:
            filter_ = Q(last_name__icontains="")
            for search in searches:
                search_filter = (
                    Q(last_name__unaccent__icontains=search)
                    | Q(first_name__unaccent__icontains=search)
                    | Q(user__first_name__unaccent__icontains=search)
                    | Q(user__last_name__unaccent__icontains=search)
                )
                filter_ = filter_ & search_filter

            queryset = queryset.filter(filter_)

        return queryset


class CurrentShareOwnerMixin:
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(share_ownerships__in=ShareOwnership.objects.active_temporal())
            .distinct()
        )


class CurrentShareOwnerListView(
    PermissionRequiredMixin,
    ShareOwnerSearchMixin,
    CurrentShareOwnerMixin,
    generic.ListView,
):
    permission_required = "coop.manage"
    model = ShareOwner
    template_name = "coop/shareowner_list.html"


class ShareOwnerExportMailchimpView(
    PermissionRequiredMixin, CurrentShareOwnerMixin, generic.list.BaseListView
):
    permission_required = "coop.manage"
    model = ShareOwner

    def get_queryset(self):
        # Only active members should be on our mailing lists
        return super().get_queryset().filter(is_investing=False)

    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="supercoop_members_mailchimp.csv"'
        writer = csv.writer(response)

        writer.writerow(["Email Address", "First Name", "Last Name", "Address", "TAGS"])
        for owner in context["object_list"]:
            if not owner.get_info().email:
                continue

            # For some weird reason the tags are in quotes
            lang_tag = ""
            if owner.preferred_language == "de":
                lang_tag = '"Deutsch"'
            if owner.preferred_language == "en":
                lang_tag = '"English"'
            writer.writerow([owner.get_info().email, "", "", "", lang_tag])

        return response

import csv
from datetime import date

import django_filters
import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import UpdateView, CreateView
from django_filters import CharFilter, ChoiceFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.coop import pdfs
from tapir.coop.forms import (
    ShareOwnershipForm,
    DraftUserForm,
    DraftUserRegisterForm,
    ShareOwnerForm,
)
from tapir.coop.models import (
    ShareOwnership,
    DraftUser,
    ShareOwner,
    UpdateShareOwnerLogEntry,
    DeleteShareOwnershipLogEntry,
    MEMBER_STATUS_CHOICES,
    MemberStatus,
    get_member_status_translation,
)
from tapir.log.models import EmailLogEntry, LogEntry
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.utils.models import copy_user_info


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


class ShareOwnershipCreateView(
    PermissionRequiredMixin, ShareOwnershipViewMixin, CreateView
):
    permission_required = "coop.manage"

    def get_initial(self):
        return {"start_date": date.today()}

    def _get_share_owner(self):
        return get_object_or_404(ShareOwner, pk=self.kwargs["shareowner_pk"])

    def form_valid(self, form):
        form.instance.owner = self._get_share_owner()
        return super().form_valid(form)


@require_POST
@csrf_protect
# Higher permission requirement since this is a destructive operation only to correct mistakes
@permission_required("coop.admin")
def share_ownership_delete(request, pk):
    share_ownership = get_object_or_404(ShareOwnership, pk=pk)
    owner = share_ownership.owner

    with transaction.atomic():
        DeleteShareOwnershipLogEntry().populate(
            share_owner=share_ownership.owner, actor=request.user, model=share_ownership
        ).save()
        share_ownership.delete()

    return redirect(owner)


class ShareOwnerDetailView(PermissionRequiredMixin, generic.DetailView):
    model = ShareOwner
    permission_required = "coop.manage"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user:
            return redirect(self.object.user)
        return super().get(request, *args, **kwargs)


class ShareOwnerUpdateView(
    PermissionRequiredMixin, UpdateViewLogMixin, generic.UpdateView
):
    permission_required = "accounts.manage"
    model = ShareOwner
    form_class = ShareOwnerForm

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                log_entry = UpdateShareOwnerLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    share_owner=form.instance,
                    actor=self.request.user,
                )
                log_entry.save()

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
def mark_shareowner_attended_welcome_session(request, pk):
    share_owner = get_object_or_404(ShareOwner, pk=pk)
    old_share_owner_dict = freeze_for_log(share_owner)

    with transaction.atomic():
        share_owner.attended_welcome_session = True
        share_owner.save()

        log_entry = UpdateShareOwnerLogEntry().populate(
            old_frozen=old_share_owner_dict,
            new_model=share_owner,
            share_owner=share_owner,
            actor=request.user,
        )
        log_entry.save()

    return redirect(share_owner.get_absolute_url())


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
        user = TapirUser()
        copy_user_info(owner, user)
        kwargs.update({"instance": user})
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            owner = self.get_shareowner()
            owner.user = form.instance
            owner.blank_info_fields()
            owner.save()

            LogEntry.objects.filter(share_owner=owner).update(
                user=form.instance, share_owner=None
            )
            return response


@require_POST
@csrf_protect
@permission_required("coop.manage")
def send_shareowner_membership_confirmation_welcome_email(request, pk):
    owner = get_object_or_404(ShareOwner, pk=pk)

    if owner.is_investing:
        template_name = "coop/email/membership_confirmation_welcome_investing.html"
    else:
        template_name = "coop/email/membership_confirmation_welcome.html"

    mail = EmailMessage(
        subject=_("Willkommen bei SuperCoop eG!"),
        body=render_to_string(template_name, {"owner": owner}),
        from_email="SuperCoop Mitgliederbüro <mitglied@supercoop.de>",
        to=[owner.get_info().email],
        bcc=["mitglied@supercoop.de"],
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

    log_entry = EmailLogEntry().populate(
        email_message=mail,
        actor=request.user,
        user=owner.user,
        share_owner=(owner if not owner.user else None),
    )
    log_entry.save()

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

        search_string = self.request.GET.get("search", "")
        is_a_search = search_string != ""

        if is_a_search and queryset.count() == 1:
            return HttpResponseRedirect(queryset.first().get_absolute_url())
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.GET.get("search", "")
        searches = [s for s in search.split(" ") if s != ""]

        if len(searches) == 1 and searches[0].isdigit():
            queryset = queryset.filter(pk=int(searches[0]))
        elif searches:
            queryset = queryset.with_name(search)

        return queryset


class CurrentShareOwnerMixin:
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(share_ownerships__in=ShareOwnership.objects.active_temporal())
            .distinct()
        )


class ShareOwnerTable(django_tables2.Table):
    class Meta:
        model = ShareOwner
        template_name = "django_tables2/bootstrap4.html"
        fields = [
            "id",
            "attended_welcome_session",
            "from_startnext",
            "ratenzahlung",
            "is_company",
        ]
        sequence = (
            "id",
            "display_name",
            "status",
            "from_startnext",
            "attended_welcome_session",
            "ratenzahlung",
            "is_company",
        )

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )
    status = django_tables2.Column(empty_values=(), orderable=False)
    email = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    phone_number = django_tables2.Column(
        empty_values=(), orderable=False, visible=False
    )
    company_name = django_tables2.Column(
        empty_values=(), orderable=False, visible=False
    )
    preferred_language = django_tables2.Column(
        empty_values=(), orderable=False, visible=False
    )

    def render_display_name(self, value, record: ShareOwner):
        return format_html(
            "<a href={}>{}</a>",
            record.get_absolute_url(),
            record.get_info().get_display_name(),
        )

    def value_display_name(self, value, record: ShareOwner):
        return record.get_info().get_display_name()

    def render_status(self, value, record: ShareOwner):
        status = record.get_member_status()
        if status == MemberStatus.SOLD:
            color = "orange"
        elif status == MemberStatus.ACTIVE:
            color = "green"
        else:
            color = "blue"

        return format_html(
            '<span style="color: {1};">{0}</span>',
            get_member_status_translation(status),
            color,
        )

    def value_status(self, value, record: ShareOwner):
        return record.get_member_status()

    def value_email(self, value, record: ShareOwner):
        return record.get_info().email

    def value_phone_number(self, value, record: ShareOwner):
        return record.get_info().phone_number

    def value_preferred_language(self, value, record: ShareOwner):
        return record.get_info().preferred_language


class ShareOwnerFilter(django_filters.FilterSet):
    class Meta:
        model = ShareOwner
        fields = [
            "from_startnext",
            "attended_welcome_session",
            "ratenzahlung",
            "is_company",
        ]

    display_name = CharFilter(method="display_name_filter", label="Name")
    status = ChoiceFilter(
        choices=MEMBER_STATUS_CHOICES,
        method="status_filter",
        label="Status",
        empty_label=_("Any"),
    )

    def display_name_filter(
        self, queryset: ShareOwner.ShareOwnerQuerySet, name, value: str
    ):
        return queryset.with_name(value)

    def status_filter(self, queryset: ShareOwner.ShareOwnerQuerySet, name, value: str):
        return queryset.with_status(value)


class ShareOwnerListView(
    PermissionRequiredMixin, FilterView, ExportMixin, SingleTableView
):
    table_class = ShareOwnerTable
    model = ShareOwner
    template_name = "coop/shareowner_list.html"
    permission_required = "coop.manage"

    filterset_class = ShareOwnerFilter

    export_formats = ["csv", "json"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_member_count"] = len(self.get_table_data())
        context["total_member_count"] = ShareOwner.objects.count()
        return context


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
            if owner.get_info().preferred_language == "de":
                lang_tag = '"Deutsch"'
            if owner.get_info().preferred_language == "en":
                lang_tag = '"English"'
            writer.writerow([owner.get_info().email, "", "", "", lang_tag])

        return response

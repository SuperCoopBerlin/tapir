import csv
import datetime

import django_filters
import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import UpdateView, FormView
from django_filters import CharFilter, ChoiceFilter, BooleanFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.coop import pdfs
from tapir.coop.config import COOP_SHARE_PRICE, on_welcome_session_attendance_update
from tapir.coop.emails.extra_shares_confirmation_email import (
    ExtraSharesConfirmationEmail,
)
from tapir.coop.emails.membership_confirmation_email_for_active_member import (
    MembershipConfirmationForActiveMemberEmail,
)
from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
    MembershipConfirmationForInvestingMemberEmail,
)
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.coop.forms import (
    ShareOwnershipForm,
    ShareOwnerForm,
    ShareOwnershipCreateMultipleForm,
)
from tapir.coop.models import (
    ShareOwnership,
    ShareOwner,
    UpdateShareOwnerLogEntry,
    DeleteShareOwnershipLogEntry,
    MEMBER_STATUS_CHOICES,
    MemberStatus,
    get_member_status_translation,
    CreateShareOwnershipsLogEntry,
    UpdateShareOwnershipLogEntry,
    ExtraSharesForAccountingRecap,
)
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.config import TAPIR_TABLE_CLASSES, TAPIR_TABLE_TEMPLATE
from tapir.core.views import TapirFormMixin
from tapir.log.models import LogEntry
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_COOP_MANAGE,
    PERMISSION_COOP_ADMIN,
    PERMISSION_ACCOUNTS_MANAGE,
)
from tapir.shifts.models import (
    ShiftUserData,
    SHIFT_USER_CAPABILITY_CHOICES,
)
from tapir.utils.models import copy_user_info
from tapir.utils.shortcuts import set_header_for_file_download, get_html_link


class ShareOwnershipViewMixin:
    model = ShareOwnership
    form_class = ShareOwnershipForm

    def get_success_url(self):
        # After successful creation or update of a ShareOwnership, return to the user overview page.
        return self.object.share_owner.get_absolute_url()


class ShareOwnershipUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateViewLogMixin,
    ShareOwnershipViewMixin,
    TapirFormMixin,
    UpdateView,
):
    permission_required = PERMISSION_COOP_MANAGE

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                UpdateShareOwnershipLogEntry().populate(
                    share_ownership=form.instance,
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    actor=self.request.user,
                    share_owner=form.instance.share_owner,
                ).save()

            return response

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        share_ownership: ShareOwnership = self.object
        context_data["page_title"] = _("Edit share: %(name)s") % {
            "name": share_ownership.share_owner.get_info().get_display_name()
        }
        context_data["card_title"] = _("Edit share: %(name)s") % {
            "name": share_ownership.share_owner.get_info().get_html_link()
        }
        return context_data


class ShareOwnershipCreateMultipleView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, FormView
):
    form_class = ShareOwnershipCreateMultipleForm
    permission_required = PERMISSION_COOP_MANAGE

    def get_share_owner(self) -> ShareOwner:
        return get_object_or_404(ShareOwner, pk=self.kwargs["shareowner_pk"])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        share_owner = self.get_share_owner()
        context_data["page_title"] = _("Add shares to %(name)s") % {
            "name": share_owner.get_info().get_display_name()
        }
        context_data["card_title"] = _("Add shares to %(name)s") % {
            "name": share_owner.get_info().get_html_link()
        }
        return context_data

    def form_valid(self, form):
        share_owner = self.get_share_owner()
        num_shares = form.cleaned_data["num_shares"]

        with transaction.atomic():
            CreateShareOwnershipsLogEntry().populate(
                actor=self.request.user,
                share_owner=share_owner,
                num_shares=num_shares,
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
            ).save()

            for _ in range(form.cleaned_data["num_shares"]):
                ShareOwnership.objects.create(
                    share_owner=share_owner,
                    amount_paid=0,
                    start_date=form.cleaned_data["start_date"],
                    end_date=form.cleaned_data["end_date"],
                )

            ExtraSharesForAccountingRecap.objects.create(
                member=share_owner,
                number_of_shares=num_shares,
                date=timezone.now().date(),
            )

        email = ExtraSharesConfirmationEmail(
            num_shares=form.cleaned_data["num_shares"], share_owner=share_owner
        )
        email.send_to_share_owner(actor=self.request.user, recipient=share_owner)

        return super().form_valid(form)

    def get_success_url(self):
        return self.get_share_owner().get_info().get_absolute_url()


@require_POST
@csrf_protect
@login_required
# Higher permission requirement since this is a destructive operation only to correct mistakes
@permission_required(PERMISSION_COOP_ADMIN)
def share_ownership_delete(request, pk):
    share_ownership = get_object_or_404(ShareOwnership, pk=pk)
    share_owner = share_ownership.share_owner

    with transaction.atomic():
        DeleteShareOwnershipLogEntry().populate(
            share_owner=share_ownership.share_owner,
            actor=request.user,
            model=share_ownership,
        ).save()
        share_ownership.delete()

    return redirect(share_owner)


class ShareOwnerDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = ShareOwner
    permission_required = PERMISSION_COOP_MANAGE

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user:
            return redirect(self.object.user)
        return super().get(request, *args, **kwargs)


class ShareOwnerUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateViewLogMixin,
    TapirFormMixin,
    generic.UpdateView,
):
    permission_required = PERMISSION_ACCOUNTS_MANAGE
    model = ShareOwner
    form_class = ShareOwnerForm

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            for callback in on_welcome_session_attendance_update:
                callback(form.instance)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                UpdateShareOwnerLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    share_owner=form.instance,
                    actor=self.request.user,
                ).save()

            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        share_owner: ShareOwner = self.object
        context["page_title"] = _("Edit member: %(name)s") % {
            "name": share_owner.get_display_name()
        }
        context["card_title"] = _("Edit member: %(name)s") % {
            "name": share_owner.get_html_link()
        }
        return context


@require_GET
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def empty_membership_agreement(request):
    filename = "Beteiligungserklärung " + settings.COOP_NAME + ".pdf"
    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)
    response.write(pdfs.get_membership_agreement_pdf().write_pdf())
    return response


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def mark_shareowner_attended_welcome_session(request, pk):
    share_owner = get_object_or_404(ShareOwner, pk=pk)
    old_frozen = freeze_for_log(share_owner)

    with transaction.atomic():
        share_owner.attended_welcome_session = True
        share_owner.save()

        for callback in on_welcome_session_attendance_update:
            callback(share_owner)

        new_frozen = freeze_for_log(share_owner)
        UpdateShareOwnerLogEntry().populate(
            old_frozen=old_frozen,
            new_frozen=new_frozen,
            share_owner=share_owner,
            actor=request.user,
        ).save()

    return redirect(share_owner.get_absolute_url())


class CreateUserFromShareOwnerView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView
):
    model = TapirUser
    template_name = "coop/create_user_from_shareowner_form.html"
    permission_required = PERMISSION_COOP_MANAGE
    fields = ["first_name", "last_name", "username"]

    def get_shareowner(self):
        return get_object_or_404(ShareOwner, pk=self.kwargs["shareowner_pk"])

    def dispatch(self, request, *args, **kwargs):
        share_owner = self.get_shareowner()
        # Not sure if 403 is the right error code here...
        if share_owner.user is not None:
            return HttpResponseForbidden("This ShareOwner already has a User")
        if share_owner.is_company:
            return HttpResponseForbidden("This ShareOwner is a company")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        share_owner = self.get_shareowner()
        user = TapirUser()
        copy_user_info(share_owner, user)
        kwargs.update({"instance": user})
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            tapir_user = form.instance
            share_owner = self.get_shareowner()
            share_owner.user = tapir_user
            share_owner.blank_info_fields()
            share_owner.save()

            for callback in on_welcome_session_attendance_update:
                callback(share_owner)

            LogEntry.objects.filter(share_owner=share_owner).update(
                user=tapir_user, share_owner=None
            )
        tapir_user.refresh_from_db()
        email = TapirAccountCreatedEmail(tapir_user=tapir_user)
        email.send_to_tapir_user(actor=self.request.user, recipient=tapir_user)
        return response


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def send_shareowner_membership_confirmation_welcome_email(request, pk):
    share_owner = get_object_or_404(ShareOwner, pk=pk)

    email = (
        MembershipConfirmationForInvestingMemberEmail
        if share_owner.is_investing
        else MembershipConfirmationForActiveMemberEmail
    )(share_owner=share_owner)
    email.send_to_share_owner(actor=request.user, recipient=share_owner)

    messages.info(request, _("Membership confirmation email sent."))

    return redirect(share_owner.get_absolute_url())


@require_GET
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def shareowner_membership_confirmation(request, pk):
    share_owner = get_object_or_404(ShareOwner, pk=pk)
    filename = (
        "Mitgliedschaftsbestätigung %s.pdf" % share_owner.get_info().get_display_name()
    )

    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)

    num_shares = (
        request.GET["num_shares"]
        if "num_shares" in request.GET.keys()
        else share_owner.get_active_share_ownerships().count()
    )
    date = (
        datetime.datetime.strptime(request.GET["date"], "%d.%m.%Y").date()
        if "date" in request.GET.keys()
        else timezone.now().date()
    )

    pdf = pdfs.get_shareowner_membership_confirmation_pdf(
        share_owner,
        num_shares=num_shares,
        date=date,
    )
    response.write(pdf.write_pdf())
    return response


@require_GET
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def shareowner_extra_shares_confirmation(request, pk):
    share_owner = get_object_or_404(ShareOwner, pk=pk)
    filename = (
        "Bestätigung Erwerb Anteile %s.pdf" % share_owner.get_info().get_display_name()
    )

    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)

    if "num_shares" not in request.GET.keys():
        raise ValidationError("Missing parameter : num_shares")
    num_shares = request.GET["num_shares"]

    if "date" not in request.GET.keys():
        raise ValidationError("Missing parameter : date")
    date = datetime.datetime.strptime(request.GET["date"], "%d.%m.%Y").date()

    pdf = pdfs.get_confirmation_extra_shares_pdf(
        share_owner,
        num_shares=num_shares,
        date=date,
    )
    response.write(pdf.write_pdf())
    return response


@require_GET
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def shareowner_membership_agreement(request, pk):
    share_owner = get_object_or_404(ShareOwner, pk=pk)
    filename = "Beteiligungserklärung %s.pdf" % share_owner.get_display_name()

    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)
    response.write(pdfs.get_membership_agreement_pdf(share_owner).write_pdf())
    return response


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
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
            "attended_welcome_session",
            "ratenzahlung",
            "is_company",
        ]
        sequence = (
            "id",
            "display_name",
            "first_name",
            "last_name",
            "street",
            "postcode",
            "city",
            "country",
            "status",
            "attended_welcome_session",
            "ratenzahlung",
            "is_company",
        )
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False, exclude_from_export=True
    )
    first_name = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    last_name = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    street = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    postcode = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    city = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    country = django_tables2.Column(empty_values=(), orderable=False, visible=False)
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
    num_shares = django_tables2.Column(empty_values=(), orderable=False, visible=False)
    join_date = django_tables2.Column(empty_values=(), orderable=False, visible=False)

    @staticmethod
    def render_display_name(value, record: ShareOwner):
        member = record.get_info()
        return get_html_link(member.get_absolute_url(), member.get_display_name())

    @staticmethod
    def value_display_name(value, record: ShareOwner):
        return record.get_info().get_display_name()

    @staticmethod
    def value_first_name(value, record: ShareOwner):
        return record.get_info().first_name

    @staticmethod
    def value_last_name(value, record: ShareOwner):
        return record.get_info().last_name

    @staticmethod
    def value_postcode(value, record: ShareOwner):
        return record.get_info().postcode

    @staticmethod
    def render_postcode(value, record: ShareOwner):
        return record.get_info().postcode

    @staticmethod
    def value_street(value, record: ShareOwner):
        return record.get_info().street

    @staticmethod
    def render_street(value, record: ShareOwner):
        return record.get_info().street

    @staticmethod
    def value_city(value, record: ShareOwner):
        return record.get_info().city

    @staticmethod
    def render_city(value, record: ShareOwner):
        return record.get_info().city

    @staticmethod
    def value_country(value, record: ShareOwner):
        return record.get_info().country

    @staticmethod
    def render_country(value, record: ShareOwner):
        return record.get_info().country

    @staticmethod
    def render_status(value, record: ShareOwner):
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

    @staticmethod
    def value_status(value, record: ShareOwner):
        return record.get_member_status()

    @staticmethod
    def value_email(value, record: ShareOwner):
        return record.get_info().email

    @staticmethod
    def value_phone_number(value, record: ShareOwner):
        return record.get_info().phone_number

    @staticmethod
    def value_preferred_language(value, record: ShareOwner):
        return record.get_info().preferred_language

    @staticmethod
    def value_num_shares(value, record: ShareOwner):
        return record.num_shares()

    @staticmethod
    def value_join_date(value, record: ShareOwner):
        ownership = record.get_oldest_active_share_ownership()
        return ownership.start_date if ownership is not None else ""


class ShareOwnerFilter(django_filters.FilterSet):
    class Meta:
        model = ShareOwner
        fields = [
            "attended_welcome_session",
            "ratenzahlung",
            "is_company",
            "paid_membership_fee",
        ]

    status = ChoiceFilter(
        choices=MEMBER_STATUS_CHOICES,
        method="status_filter",
        label=_("Status"),
        empty_label=_("Any"),
    )
    shift_attendance_mode = ChoiceFilter(
        choices=ShiftUserData.SHIFT_ATTENDANCE_MODE_CHOICES,
        method="shift_attendance_mode_filter",
        label=_("Shift Status"),
    )
    registered_to_slot_with_capability = ChoiceFilter(
        choices=[
            (capability, capability_name)
            for capability, capability_name in SHIFT_USER_CAPABILITY_CHOICES.items()
        ],
        method="registered_to_slot_with_capability_filter",
        label=_("Is registered to a slot that requires a qualification"),
    )
    has_capability = ChoiceFilter(
        choices=[
            (capability, capability_name)
            for capability, capability_name in SHIFT_USER_CAPABILITY_CHOICES.items()
        ],
        method="has_capability_filter",
        label=_("Has qualification"),
    )
    not_has_capability = ChoiceFilter(
        choices=[
            (capability, capability_name)
            for capability, capability_name in SHIFT_USER_CAPABILITY_CHOICES.items()
        ],
        method="not_has_capability_filter",
        label=_("Does not have qualification"),
    )
    has_tapir_account = BooleanFilter(
        method="has_tapir_account_filter", label=_("Has a Tapir account")
    )
    # Théo 17.09.21 : It would be nicer to get the values from the DB, but that raises exceptions
    # when creating a brand new docker instance, because the corresponding table doesn't exist yet.
    abcd_week = ChoiceFilter(
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
        method="abcd_week_filter",
        label=_("ABCD Week"),
    )
    has_unpaid_shares = BooleanFilter(
        method="has_unpaid_shares_filter", label=_("Has unpaid shares")
    )
    is_fully_paid = BooleanFilter(
        method="is_fully_paid_filter", label=_("Is fully paid")
    )
    display_name = CharFilter(
        method="display_name_filter", label=_("Name or member ID")
    )

    @staticmethod
    def display_name_filter(queryset: ShareOwner.ShareOwnerQuerySet, name, value: str):
        # This is an ugly hack to enable searching by Mitgliedsnummer from the
        # one-stop search box in the top right
        if value.isdigit():
            return queryset.filter(id=int(value))

        return queryset.with_name(value).distinct()

    @staticmethod
    def status_filter(queryset: ShareOwner.ShareOwnerQuerySet, name, value: str):
        return queryset.with_status(value).distinct()

    @staticmethod
    def shift_attendance_mode_filter(
        queryset: ShareOwner.ShareOwnerQuerySet, name, value: str
    ):
        return queryset.filter(
            user__in=TapirUser.objects.with_shift_attendance_mode(value)
        ).distinct()

    @staticmethod
    def registered_to_slot_with_capability_filter(
        queryset: ShareOwner.ShareOwnerQuerySet, name, value: str
    ):
        return queryset.filter(
            user__in=TapirUser.objects.registered_to_shift_slot_with_capability(value)
        ).distinct()

    @staticmethod
    def has_capability_filter(
        queryset: ShareOwner.ShareOwnerQuerySet, name, value: str
    ):
        return queryset.filter(
            user__in=TapirUser.objects.has_capability(value)
        ).distinct()

    @staticmethod
    def not_has_capability_filter(
        queryset: ShareOwner.ShareOwnerQuerySet, name, value: str
    ):
        return queryset.exclude(
            user__in=TapirUser.objects.has_capability(value)
        ).distinct()

    @staticmethod
    def has_tapir_account_filter(
        queryset: ShareOwner.ShareOwnerQuerySet, name, value: bool
    ):
        return queryset.exclude(user__isnull=value).distinct()

    @staticmethod
    def abcd_week_filter(queryset: ShareOwner.ShareOwnerQuerySet, name, value: str):
        return queryset.filter(
            user__shift_attendance_templates__slot_template__shift_template__group__name=value
        ).distinct()

    @staticmethod
    def has_unpaid_shares_filter(
        queryset: ShareOwner.ShareOwnerQuerySet, name, value: bool
    ):
        unpaid_shares = ShareOwnership.objects.filter(
            amount_paid__lt=COOP_SHARE_PRICE, share_owner__in=queryset
        )

        if value:
            return queryset.filter(share_ownerships__in=unpaid_shares).distinct()
        else:
            return queryset.exclude(share_ownerships__in=unpaid_shares).distinct()

    def is_fully_paid_filter(
        self, queryset: ShareOwner.ShareOwnerQuerySet, name, value: bool
    ):
        return queryset.with_fully_paid(value)


class ShareOwnerListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FilterView,
    ExportMixin,
    SingleTableView,
):
    table_class = ShareOwnerTable
    model = ShareOwner
    template_name = "coop/shareowner_list.html"
    permission_required = PERMISSION_COOP_MANAGE

    filterset_class = ShareOwnerFilter

    export_formats = ["csv", "json"]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object_list.count() == 1:
            return HttpResponseRedirect(
                self.get_table_data().first().get_absolute_url()
            )
        return response

    def get_queryset(self):
        queryset = ShareOwner.objects.prefetch_related(
            "share_ownerships"
        ).prefetch_related("user")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtered_member_count"] = self.object_list.count()
        context["total_member_count"] = ShareOwner.objects.count()
        return context


class ShareOwnerExportMailchimpView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CurrentShareOwnerMixin,
    generic.list.BaseListView,
):
    permission_required = PERMISSION_COOP_MANAGE
    model = ShareOwner

    def get_queryset(self):
        # Only active members should be on our mailing lists
        return super().get_queryset().filter(is_investing=False)

    @staticmethod
    def render_to_response(context, **response_kwargs):
        response = HttpResponse(content_type="text/csv")
        set_header_for_file_download(response, "members_mailchimp.csv")
        writer = csv.writer(response)

        writer.writerow(
            [
                "Email Address",
                "First Name",
                "Last Name",
                "Address",
                "Tags",
            ]
        )
        for share_owner in context["object_list"]:
            if not share_owner.get_info().email:
                continue

            # For some weird reason the tags are in quotes
            lang_tag = ""
            if share_owner.get_info().preferred_language == "de":
                lang_tag = '"Deutsch"'
            if share_owner.get_info().preferred_language == "en":
                lang_tag = '"English"'
            writer.writerow(
                [
                    share_owner.get_info().email,
                    share_owner.get_info().first_name,
                    share_owner.get_info().last_name,
                    share_owner.get_info().street,
                    lang_tag,
                ]
            )

        return response


class MatchingProgramTable(django_tables2.Table):
    class Meta:
        model = ShareOwner
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "willing_to_gift_a_share",
        ]
        sequence = (
            "display_name",
            "willing_to_gift_a_share",
        )
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )

    @staticmethod
    def render_display_name(value, record: ShareOwner):
        member = record.get_info()
        return get_html_link(member.get_absolute_url(), member.get_display_name())

    @staticmethod
    def render_willing_to_gift_a_share(value, record: ShareOwner):
        if record.willing_to_gift_a_share is None:
            return pgettext_lazy(
                context="Willing to give a share",
                message="No",
            )
        return record.willing_to_gift_a_share.strftime("%d.%m.%Y")


class MatchingProgramListView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleTableView
):
    permission_required = PERMISSION_COOP_MANAGE
    model = ShareOwner
    template_name = "coop/matching_program.html"
    table_class = MatchingProgramTable

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(willing_to_gift_a_share=None)
            .order_by("willing_to_gift_a_share")
            .prefetch_related("user")
        )

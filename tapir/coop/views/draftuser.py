import django_filters
import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

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
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.core.config import TAPIR_TABLE_TEMPLATE, TAPIR_TABLE_CLASSES
from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.utils.models import copy_user_info
from tapir.utils.shortcuts import set_header_for_file_download
from tapir.utils.user_utils import UserUtils


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
            "name": UserUtils.build_display_name_for_viewer(
                draft_user, self.request.user
            )
        }
        context["card_title"] = _("Edit applicant: %(name)s") % {
            "name": UserUtils.build_html_link_for_viewer(draft_user, self.request.user)
        }
        return context


class DraftUserDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    permission_required = PERMISSION_COOP_MANAGE
    model = DraftUser

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        draft_user: DraftUser = self.object

        filters = Q(last_name=draft_user.last_name) | Q(email=draft_user.email)
        if draft_user.phone_number:
            filters |= Q(phone_number=draft_user.phone_number)
        if draft_user.street:
            filters |= Q(street=draft_user.street)
        context_data["similar_members"] = ShareOwner.objects.filter(filters)

        return context_data


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
    filename = "Beteiligungserklärung %s.pdf" % (
        UserUtils.build_display_name_for_viewer(draft_user, request.user)
    )

    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)
    response.write(pdfs.get_membership_agreement_pdf(draft_user).write_pdf())
    return response


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def mark_signed_membership_agreement(_, pk):
    user = DraftUser.objects.get(pk=pk)
    user.signed_membership_agreement = True
    user.save()

    return redirect(user)


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def mark_attended_welcome_session(_, pk):
    user = DraftUser.objects.get(pk=pk)
    user.attended_welcome_session = True
    user.save()

    return redirect(user)


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_COOP_MANAGE)
def register_draftuser_payment(_, pk):
    draft = get_object_or_404(DraftUser, pk=pk)
    draft.paid_membership_fee = True
    draft.save()
    return redirect(draft.get_absolute_url())


class CreateShareOwnerFromDraftUserView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.RedirectView
):
    permission_required = [PERMISSION_COOP_MANAGE]

    def get_redirect_url(self, *args, **kwargs):
        draft_user = get_object_or_404(DraftUser, pk=self.kwargs["pk"])
        return (
            draft_user.share_owner.get_absolute_url()
            if draft_user.share_owner
            else draft_user.get_absolute_url()
        )

    def get(self, request, *args, **kwargs):
        draft_user = get_object_or_404(DraftUser, pk=self.kwargs["pk"])

        if not draft_user.can_create_user():
            messages.error(
                request,
                mark_safe(
                    _("Can't create member: ")
                    + "<br />"
                    + draft_user.must_solve_before_creating_share_owner_display()
                ),
            )
            return super().get(request, args, kwargs)

        with transaction.atomic():
            share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
            draft_user.share_owner = share_owner
            draft_user.save()

            NewMembershipsForAccountingRecap.objects.create(
                member=share_owner,
                number_of_shares=NumberOfSharesService.get_number_of_active_shares(
                    share_owner
                ),
                date=timezone.now().date(),
            )

            email = (
                MembershipConfirmationForInvestingMemberEmail
                if share_owner.is_investing
                else MembershipConfirmationForActiveMemberEmail
            )(share_owner=share_owner)
            email.send_to_share_owner(actor=request.user, recipient=share_owner)

        return super().get(request, args, kwargs)


def create_share_owner_and_shares_from_draft_user(draft_user: DraftUser) -> ShareOwner:
    share_owner = ShareOwner(
        is_company=False,
        is_investing=draft_user.is_investing,
        ratenzahlung=draft_user.ratenzahlung,
        attended_welcome_session=draft_user.attended_welcome_session,
        paid_membership_fee=draft_user.paid_membership_fee,
    )

    copy_user_info(draft_user, share_owner)
    share_owner.save()

    ShareOwnership.objects.bulk_create(
        [
            ShareOwnership(
                share_owner=share_owner,
                start_date=timezone.now().date(),
                amount_paid=(COOP_SHARE_PRICE if draft_user.paid_shares else 0),
            )
            for _ in range(0, draft_user.num_shares)
        ]
    )

    return share_owner


class DraftUserTable(django_tables2.Table):
    class Meta:
        model = DraftUser
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "created_at",
        ]
        sequence = (
            "display_name",
            "share_owner_can_be_created",
            "created_at",
        )
        order_by = "-created_at"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(),
        verbose_name=_("Name"),
        orderable=False,
    )
    share_owner_can_be_created = django_tables2.Column(
        empty_values=(),
        verbose_name=_("Member can be created"),
        orderable=False,
        exclude_from_export=True,
    )

    def before_render(self, request):
        self.request = request

    @staticmethod
    def render_share_owner_can_be_created(value, record: DraftUser):
        return _("Yes") if record.can_create_user() else _("No")

    def value_display_name(self, value, record: DraftUser):
        return UserUtils.build_display_name_for_viewer(record, self.request.user)

    def render_display_name(self, value, record: DraftUser):
        return UserUtils.build_html_link_for_viewer(record, self.request.user)

    @staticmethod
    def render_created_at(value, record: DraftUser):
        return record.created_at.strftime("%d.%m.%Y %H:%M")


class DraftUserFilter(django_filters.FilterSet):
    class Meta:
        model = DraftUser
        fields = [
            "is_investing",
            "attended_welcome_session",
            "signed_membership_agreement",
        ]

    def __init__(self, *args, **kwargs):
        super(DraftUserFilter, self).__init__(*args, **kwargs)

    share_owner_can_be_created = django_filters.BooleanFilter(
        method="share_owner_can_be_created_filter", label=_("Member can be created")
    )

    @staticmethod
    def share_owner_can_be_created_filter(queryset: QuerySet, _, can_be_created: bool):
        draft_user_ids = [
            draft_user.id
            for draft_user in queryset
            if draft_user.can_create_user() == can_be_created
        ]
        return queryset.filter(id__in=draft_user_ids)


class DraftUserListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FilterView,
    ExportMixin,
    SingleTableView,
):
    table_class = DraftUserTable
    model = DraftUser
    template_name = "coop/draftuser_list.html"
    filterset_class = DraftUserFilter
    export_formats = ["csv", "json"]
    permission_required = [PERMISSION_COOP_MANAGE]

    def get_queryset(self):
        return super().get_queryset().filter(share_owner__isnull=True)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["filtered_draftuser_count"] = self.object_list.count()
        context_data["total_draftuser_count"] = DraftUser.objects.count()
        return context_data

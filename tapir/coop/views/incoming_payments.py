import django_filters
import django_tables2
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django_filters.views import FilterView
from django_tables2 import SingleTableView

from tapir.accounts.models import TapirUser
from tapir.coop.forms import IncomingPaymentForm
from tapir.coop.models import (
    IncomingPayment,
    ShareOwner,
    CreatePaymentLogEntry,
    UpdateIncomingPaymentLogEntry,
    DeleteIncomingPaymentLogEntry,
)
from tapir.core.config import TAPIR_TABLE_CLASSES, TAPIR_TABLE_TEMPLATE
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_COOP_VIEW,
    PERMISSION_ACCOUNTING_MANAGE,
    PERMISSION_ACCOUNTING_VIEW,
    PERMISSION_COOP_ADMIN,
)
from tapir.utils.filters import ShareOwnerModelChoiceFilter, TapirUserModelChoiceFilter
from tapir.utils.forms import DateFromToRangeFilterTapir
from tapir.utils.user_utils import UserUtils


class IncomingPaymentTable(django_tables2.Table):
    class Meta:
        model = IncomingPayment
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
            "paying_member",
            "credited_member",
            "amount",
            "payment_date",
            "creation_date",
            "comment",
            "created_by",
        ]
        order_by = "-payment_date"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    id = django_tables2.Column(verbose_name=_("Payment ID"))
    actions = django_tables2.TemplateColumn(
        template_name="coop/incoming_payments_actions_column.html",
        verbose_name="Actions",
        orderable=False,
        exclude_from_export=True,
        visible=False,
    )

    def before_render(self, request):
        self.request = request
        if request.user.has_perm(PERMISSION_COOP_ADMIN):
            self.columns.show("actions")

    def render_id(self, value, record: IncomingPayment):
        return f"#{record.id}"

    def render_member(self, logged_in_member: TapirUser, other_member: ShareOwner):
        if logged_in_member.share_owner == other_member or logged_in_member.has_perm(
            PERMISSION_ACCOUNTING_VIEW
        ):
            other_member = other_member.get_info()
            return UserUtils.build_html_link_for_viewer(other_member, logged_in_member)
        return _("Other member")

    def render_paying_member(self, value, record: IncomingPayment):
        return self.render_member(self.request.user, record.paying_member)

    def render_credited_member(self, value, record: IncomingPayment):
        return self.render_member(self.request.user, record.credited_member)

    def render_created_by(self, value, record: IncomingPayment):
        return self.render_member(self.request.user, record.created_by.share_owner)

    def render_payment_date(self, value, record: IncomingPayment):
        return record.payment_date.strftime("%d.%m.%Y")

    def render_creation_date(self, value, record: IncomingPayment):
        return record.creation_date.strftime("%d.%m.%Y")


class IncomingPaymentFilter(django_filters.FilterSet):
    class Meta:
        model = IncomingPayment
        fields = []

    payment_date = DateFromToRangeFilterTapir(
        field_name="payment_date",
    )
    creation_date = DateFromToRangeFilterTapir(
        field_name="creation_date",
    )

    paying_member = ShareOwnerModelChoiceFilter()
    credited_member = ShareOwnerModelChoiceFilter()
    created_by = TapirUserModelChoiceFilter()


class IncomingPaymentListView(LoginRequiredMixin, FilterView, SingleTableView):
    table_class = IncomingPaymentTable
    model = IncomingPayment
    template_name = "coop/incoming_payment_list.html"

    filterset_class = IncomingPaymentFilter

    def get_queryset(self):
        queryset = IncomingPayment.objects.all()
        if not self.request.user.has_perm(PERMISSION_ACCOUNTING_VIEW):
            tapir_user: TapirUser = self.request.user
            logged_in_share_owner = tapir_user.share_owner
            return queryset.filter(
                Q(paying_member=logged_in_share_owner)
                | Q(credited_member=logged_in_share_owner)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["enable_filter"] = self.request.user.has_perm(PERMISSION_COOP_VIEW)
        return context_data


class IncomingPaymentCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, generic.CreateView
):
    permission_required = PERMISSION_ACCOUNTING_MANAGE
    model = IncomingPayment
    form_class = IncomingPaymentForm

    def get_success_url(self):
        return reverse("coop:incoming_payment_list")

    def form_valid(self, form):
        with transaction.atomic():
            payment: IncomingPayment = form.instance
            payment.creation_date = timezone.now().date()
            payment.created_by = self.request.user
            payment.save()
            CreatePaymentLogEntry().populate(
                actor=self.request.user,
                share_owner=form.cleaned_data["credited_member"],
                amount=form.cleaned_data["amount"],
                payment_date=form.cleaned_data["payment_date"],
            ).save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["page_title"] = _("Register payment")
        context["card_title"] = _("Register a new incoming payment")
        return context


class IncomingPaymentEditView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    UpdateViewLogMixin,
    generic.UpdateView,
):
    permission_required = PERMISSION_COOP_ADMIN
    model = IncomingPayment
    form_class = IncomingPaymentForm

    def get_success_url(self):
        return reverse("coop:incoming_payment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["page_title"] = _("Edit payment")
        context["card_title"] = _("Edit payment")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Payment updated."))
        new_frozen = freeze_for_log(form.instance)
        if self.old_object_frozen != new_frozen:
            UpdateIncomingPaymentLogEntry().populate(
                old_frozen=self.old_object_frozen,
                new_frozen=new_frozen,
                share_owner=form.instance.paying_member,
                actor=self.request.user,
            ).save()
        return super().form_valid(form)


class IncomingPaymentDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView
):
    permission_required = PERMISSION_COOP_ADMIN
    model = IncomingPayment
    template_name = "coop/confirm_delete_incoming_payment.html"

    def get_success_url(self):
        return reverse("coop:incoming_payment_list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Payment deleted"))
        DeleteIncomingPaymentLogEntry().populate(
            share_owner=self.object.paying_member, actor=request.user, model=self.object
        ).save()
        return response

import django_filters
import django_tables2
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
from tapir.coop.models import IncomingPayment, ShareOwner, CreatePaymentLogEntry
from tapir.core.config import TAPIR_TABLE_CLASSES, TAPIR_TABLE_TEMPLATE
from tapir.core.views import TapirFormMixin
from tapir.settings import (
    PERMISSION_COOP_VIEW,
    PERMISSION_ACCOUNTING_MANAGE,
    PERMISSION_ACCOUNTING_VIEW,
)
from tapir.utils.filters import ShareOwnerModelChoiceFilter, TapirUserModelChoiceFilter
from tapir.utils.forms import DateFromToRangeFilterTapir
from tapir.utils.shortcuts import get_html_link


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

    def before_render(self, request):
        self.request = request

    def render_id(self, value, record: IncomingPayment):
        return f"#{record.id}"

    def render_member(self, logged_in_member: TapirUser, other_member: ShareOwner):
        if logged_in_member.share_owner == other_member or logged_in_member.has_perm(
            PERMISSION_COOP_VIEW
        ):
            other_member = other_member.get_info()
            return get_html_link(
                other_member.get_absolute_url(),
                f"{other_member.get_display_name()} #{other_member.id}",
            )
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

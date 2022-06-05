import django_filters
import django_tables2
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views import generic
from django_filters.views import FilterView
from django_tables2 import SingleTableView

from tapir.coop.forms import IncomingPaymentForm
from tapir.coop.models import IncomingPayment


class IncomingPaymentTable(django_tables2.Table):
    class Meta:
        model = IncomingPayment
        template_name = "django_tables2/bootstrap4.html"
        fields = [
            "paying_member",
            "credited_member",
            "amount",
            "payment_date",
            "creation_date",
            "comment",
            "created_by",
        ]
        order_by = "payment_date"

    # display_name = django_tables2.Column(
    #     empty_values=(), verbose_name="Name", orderable=False
    # )
    #
    # def render_display_name(self, value, record: ShareOwner):
    #     return format_html(
    #         "<a href={}>{}</a>",
    #         record.get_absolute_url(),
    #         record.get_info().get_display_name(),
    #     )
    #
    # def value_display_name(self, value, record: ShareOwner):
    #     return record.get_info().get_display_name()


class IncomingPaymentFilter(django_filters.FilterSet):
    class Meta:
        model = IncomingPayment
        fields = [
            "paying_member",
            "credited_member",
            "created_by",
            "payment_date",  # TODO Théo 04.06.22 : use from/to date instead of an exact one
            "creation_date",
        ]


class IncomingPaymentListView(PermissionRequiredMixin, FilterView, SingleTableView):
    table_class = IncomingPaymentTable
    model = IncomingPayment
    template_name = "coop/incoming_payment_list.html"
    permission_required = "coop.manage"

    filterset_class = IncomingPaymentFilter


class IncomingPaymentCreateView(PermissionRequiredMixin, generic.CreateView):
    permission_required = "coop.manage"
    model = IncomingPayment
    form_class = IncomingPaymentForm

    def get_success_url(self):
        return reverse("coop:incoming_payment_list")

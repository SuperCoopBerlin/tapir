import django_filters
import django_tables2
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django_filters import CharFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableView

from tapir.coop.models import ShareOwner
from tapir.core.config import TAPIR_TABLE_TEMPLATE, TAPIR_TABLE_CLASSES
from tapir.settings import PERMISSION_WELCOMEDESK_VIEW
from tapir.shifts.models import ShiftAttendanceMode, ShiftAttendanceTemplate
from tapir.utils.shortcuts import get_html_link


class ShareOwnerTableWelcomeDesk(django_tables2.Table):
    class Meta:
        model = ShareOwner
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
        ]
        sequence = (
            "id",
            "display_name",
        )
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )

    @staticmethod
    def render_display_name(value, record: ShareOwner):
        return get_html_link(
            reverse("welcomedesk:welcome_desk_share_owner", args=[record.pk]),
            record.get_info().get_display_name(),
        )


class ShareOwnerFilterWelcomeDesk(django_filters.FilterSet):
    display_name = CharFilter(
        method="display_name_filter", label=_("Name or member ID")
    )

    @staticmethod
    def display_name_filter(queryset: ShareOwner.ShareOwnerQuerySet, name, value: str):
        if not value:
            return queryset.none()

        if value.isdigit():
            return queryset.filter(id=int(value))

        return queryset.with_name(value)


class WelcomeDeskSearchView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = PERMISSION_WELCOMEDESK_VIEW
    template_name = "welcomedesk/welcome_desk_search.html"
    table_class = ShareOwnerTableWelcomeDesk
    model = ShareOwner
    filterset_class = ShareOwnerFilterWelcomeDesk

    def get_queryset(self):
        return super().get_queryset().prefetch_related("user")


class WelcomeDeskShareOwnerView(PermissionRequiredMixin, generic.DetailView):
    model = ShareOwner
    template_name = "welcomedesk/welcome_desk_share_owner.html"
    permission_required = PERMISSION_WELCOMEDESK_VIEW
    context_object_name = "share_owner"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)
        share_owner: ShareOwner = context_data["share_owner"]

        context_data["can_shop"] = share_owner.can_shop()

        context_data["missing_account"] = share_owner.user is None
        if context_data["missing_account"]:
            return context_data

        context_data[
            "shift_balance_not_ok"
        ] = not share_owner.user.shift_user_data.is_balance_ok()

        context_data["must_register_to_a_shift"] = (
            share_owner.user.shift_user_data.attendance_mode
            == ShiftAttendanceMode.REGULAR
            and not ShiftAttendanceTemplate.objects.filter(
                user=share_owner.user
            ).exists()
            and not share_owner.user.shift_user_data.is_currently_exempted_from_shifts()
        )

        return context_data

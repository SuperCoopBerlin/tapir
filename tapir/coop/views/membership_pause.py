import django_filters
import django_tables2
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.coop.forms import MembershipPauseForm
from tapir.coop.models import (
    MembershipPause,
    MembershipPauseUpdatedLogEntry,
    MembershipPauseCreatedLogEntry,
)
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.core.config import TAPIR_TABLE_TEMPLATE, TAPIR_TABLE_CLASSES
from tapir.core.templatetags.core import tapir_button_link_to_action
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.utils.user_utils import UserUtils


class MembershipPauseTable(django_tables2.Table):
    class Meta:
        model = MembershipPause
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
            "share_owner",
            "description",
            "start_date",
            "end_date",
        ]
        sequence = (
            "id",
            "share_owner",
            "description",
            "start_date",
            "end_date",
        )
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    edit_button = django_tables2.Column(
        empty_values=(),
        verbose_name="Actions",
        orderable=False,
        exclude_from_export=True,
    )

    def before_render(self, request):
        self.request = request

    def render_share_owner(self, value, record: MembershipPause):
        return UserUtils.build_html_link_for_viewer(
            record.share_owner, self.request.user
        )

    def value_share_owner(self, value, record: MembershipPause):
        return record.share_owner.get_member_number()

    def render_start_date(self, value, record: MembershipPause):
        return record.start_date.strftime("%d.%m.%Y")

    def render_end_date(self, value, record: MembershipPause):
        return record.end_date.strftime("%d.%m.%Y") if record.end_date else _("None")

    def render_edit_button(self, value, record: MembershipPause):
        return format_html(
            "<a href='{}' class='{}'>{}</a>",
            reverse_lazy("coop:membership_pause_edit", args=[record.pk]),
            tapir_button_link_to_action(),
            format_html("<span class='material-icons'>edit</span>"),
        )


class MembershipPauseFilter(django_filters.FilterSet):
    class Meta:
        model = MembershipPause
        fields = []

    is_active = django_filters.BooleanFilter(
        method="is_active_filter", label="Is active"
    )

    @staticmethod
    def is_active_filter(queryset: QuerySet, name, is_active: bool):
        if is_active:
            return queryset.active_temporal()
        else:
            return queryset.exclude(id__in=queryset.active_temporal())


class MembershipPauseListView(
    LoginRequiredMixin,
    FilterView,
    ExportMixin,
    SingleTableView,
):
    table_class = MembershipPauseTable
    model = MembershipPause
    template_name = "coop/membership_pause/membership_pause_list.html"
    filterset_class = MembershipPauseFilter
    export_formats = ["csv", "json"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user: TapirUser = self.request.user
        if not user.has_perm(PERMISSION_COOP_MANAGE):
            queryset = queryset.filter(share_owner=user.share_owner)
        queryset = queryset.prefetch_related("share_owner__user")
        return queryset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["filtered_pause_count"] = self.object_list.count()
        context_data["total_pause_count"] = MembershipPause.objects.count()
        return context_data


class MembershipPauseCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = MembershipPause
    permission_required = PERMISSION_COOP_MANAGE
    form_class = MembershipPauseForm
    success_url = reverse_lazy("coop:membership_pauses")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Create a new membership pause")
        context_data["card_title"] = context_data["page_title"]
        return context_data

    def form_valid(self, form):
        with transaction.atomic():
            result = super().form_valid(form)

            MembershipPauseService.on_pause_created_or_updated(form.instance)

            MembershipPauseCreatedLogEntry().populate(
                pause=form.instance,
                actor=self.request.user,
            ).save()

        return result


class MembershipPauseEditView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    UpdateViewLogMixin,
    UpdateView,
):
    model = MembershipPause
    permission_required = PERMISSION_COOP_MANAGE
    form_class = MembershipPauseForm
    success_url = reverse_lazy("coop:membership_pauses")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Edit membership pause: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                person=self.object.share_owner, viewer=self.request.user
            )
        }
        context_data["card_title"] = _("Edit membership pause: %(name)s") % {
            "name": UserUtils.build_html_link_for_viewer(
                person=self.object.share_owner, viewer=self.request.user
            )
        }
        return context_data

    def form_valid(self, form):
        with transaction.atomic():
            result = super().form_valid(form)

            MembershipPauseService.on_pause_created_or_updated(form.instance)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                MembershipPauseUpdatedLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    pause=form.instance,
                    actor=self.request.user,
                ).save()

        return result

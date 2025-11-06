import django_filters
import django_tables2
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    FormView,
)
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.coop.models import MembershipPause
from tapir.core.config import TAPIR_TABLE_TEMPLATE, TAPIR_TABLE_CLASSES
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import PERMISSION_SHIFTS_EXEMPTIONS, PERMISSION_COOP_MANAGE, EMAIL_ADDRESS_MEMBER_OFFICE
from tapir.shifts.forms import (
    ShiftExemptionForm,
    ConvertShiftExemptionToMembershipPauseForm,
)
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftUserData,
    ShiftExemption,
    CreateExemptionLogEntry,
    UpdateExemptionLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.utils.user_utils import UserUtils


class CreateShiftExemptionView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = ShiftExemption
    form_class = ShiftExemptionForm
    permission_required = PERMISSION_SHIFTS_EXEMPTIONS

    def get_target_user_data(self) -> ShiftUserData:
        return ShiftUserData.objects.get(pk=self.kwargs["shift_user_data_pk"])

    def get_form_kwargs(self, *args, **kwargs):
        self.object = self.model()
        self.object.shift_user_data = self.get_target_user_data()
        # Will pass the object to the form
        return super().get_form_kwargs(*args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            exemption: ShiftExemption = form.instance
            self.cancel_attendances_covered_by_exemption(exemption, self.request.user)
            CreateExemptionLogEntry().populate(
                start_date=exemption.start_date,
                end_date=exemption.end_date,
                actor=self.request.user,
                tapir_user=exemption.shift_user_data.user,
            ).save()
            return super().form_valid(form)

    @staticmethod
    def cancel_attendances_covered_by_exemption(
        exemption: ShiftExemption, actor: TapirUser | User
    ):
        tapir_user = exemption.shift_user_data.user
        for attendance in ShiftExemption.get_attendances_cancelled_by_exemption(
            user=tapir_user,
            start_date=exemption.start_date,
            end_date=exemption.end_date,
        ):
            attendance.state = ShiftAttendance.State.CANCELLED
            attendance.excused_reason = (
                _("Is covered by shift exemption: ") + exemption.description
            )
            attendance.save()

        if ShiftExemption.must_unregister_from_abcd_shift(
            start_date=exemption.start_date, end_date=exemption.end_date
        ):
            attendance_templates_to_delete = ShiftAttendanceTemplate.objects.filter(
                user=tapir_user
            )
            for attendance_template in attendance_templates_to_delete:
                DeleteShiftAttendanceTemplateLogEntry().populate(
                    actor=actor,
                    tapir_user=tapir_user,
                    shift_attendance_template=attendance_template,
                    comment="Unregistered because of shift exemption",
                ).save()
            attendance_templates_to_delete.delete()

    def get_success_url(self):
        return self.get_target_user_data().user.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tapir_user = self.get_target_user_data().user
        context["page_title"] = _("Shift exemption: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                tapir_user, self.request.user
            )
        }
        context["card_title"] = _("Create shift exemption for: %(link)s") % {
            "link": UserUtils.build_html_link_for_viewer(tapir_user, self.request.user)
        }
        return context


class EditShiftExemptionView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    UpdateViewLogMixin,
    UpdateView,
):
    model = ShiftExemption
    form_class = ShiftExemptionForm
    permission_required = PERMISSION_SHIFTS_EXEMPTIONS

    def get_success_url(self):
        return reverse("shifts:shift_exemption_list")

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            exemption: ShiftExemption = form.instance
            CreateShiftExemptionView.cancel_attendances_covered_by_exemption(
                exemption, self.request.user
            )

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                UpdateExemptionLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    tapir_user=ShiftUserData.objects.get(
                        shift_exemptions=self.kwargs["pk"]
                    ).user,
                    actor=self.request.user,
                ).save()

            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tapir_user: TapirUser = self.object.shift_user_data.user
        context["page_title"] = _("Shift exemption: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                tapir_user, self.request.user
            )
        }
        context["card_title"] = _("Edit shift exemption for: %(link)s") % {
            "link": UserUtils.build_html_link_for_viewer(tapir_user, self.request.user)
        }
        return context


class ShiftExemptionTable(django_tables2.Table):
    class Meta:
        model = ShiftExemption
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
            "shift_user_data",
            "description",
            "start_date",
            "end_date",
        ]
        sequence = (
            "id",
            "shift_user_data",
            "description",
            "start_date",
            "end_date",
        )
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    shift_user_data = django_tables2.Column(verbose_name="Member")

    actions = django_tables2.TemplateColumn(
        template_name="shifts/exemption_table_actions_column.html",
        verbose_name="Actions",
        orderable=False,
        exclude_from_export=True,
    )

    def before_render(self, request):
        self.request = request

    def render_shift_user_data(self, value, record: ShiftExemption):
        return UserUtils.build_html_link_for_viewer(
            record.shift_user_data.user, self.request.user
        )

    def value_shift_user_data(self, value, record: ShiftExemption):
        return record.shift_user_data.user.get_member_number()

    def render_start_date(self, value, record: ShiftExemption):
        return record.start_date.strftime("%d.%m.%Y")

    def render_end_date(self, value, record: ShiftExemption):
        return record.end_date.strftime("%d.%m.%Y") if record.end_date else _("None")


class ShiftExemptionFilter(django_filters.FilterSet):
    class Meta:
        model = ShiftExemption
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


class ShiftExemptionListView(
    LoginRequiredMixin,
    FilterView,
    ExportMixin,
    SingleTableView,
):
    table_class = ShiftExemptionTable
    model = ShiftExemption
    template_name = "shifts/shiftexemption_list.html"
    filterset_class = ShiftExemptionFilter
    export_formats = ["csv", "json"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm(PERMISSION_SHIFTS_EXEMPTIONS):
            queryset = queryset.filter(
                shift_user_data__id=self.request.user.shift_user_data.id
            )
        shift_user_data_id = self.request.GET.get("shift_user_data_id", None)
        if shift_user_data_id is not None:
            queryset = queryset.filter(shift_user_data__id=shift_user_data_id)
        queryset = queryset.prefetch_related("shift_user_data__user__share_owner")
        return queryset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["filtered_exemption_count"] = self.object_list.count()
        context_data["total_exemption_count"] = ShiftExemption.objects.count()
        context_data["can_create_exemption"] = self.request.user.has_perm(PERMISSION_SHIFTS_EXEMPTIONS)
        context_data["EMAIL_ADDRESS_MEMBER_OFFICE"] = EMAIL_ADDRESS_MEMBER_OFFICE
        shift_user_data_id = self.request.GET.get("shift_user_data_id", None)
        if shift_user_data_id is not None:
            context_data["shift_user_data"] = ShiftUserData.objects.get(
                pk=shift_user_data_id
            )
        return context_data


class ConvertShiftExemptionToMembershipPauseView(
    LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    permission_required = [PERMISSION_SHIFTS_EXEMPTIONS, PERMISSION_COOP_MANAGE]
    form_class = ConvertShiftExemptionToMembershipPauseForm
    template_name = "shifts/convert_exemption_to_pause_form.html"

    def get_success_url(self):
        return reverse("shifts:shift_exemption_list")

    def get_exemption(self):
        return get_object_or_404(ShiftExemption, pk=self.kwargs["pk"])

    def form_valid(self, form):
        result = super().form_valid(form)
        exemption = self.get_exemption()
        with transaction.atomic():
            MembershipPause.objects.create(
                share_owner=exemption.shift_user_data.user.share_owner,
                start_date=exemption.start_date,
                end_date=exemption.end_date,
                description=f"Converted from a shift exemption : {exemption.description}",
            )
            exemption.delete()

        messages.info(self.request, _("Shift exemption converted to membership pause."))
        return result

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["exemption"] = self.get_exemption()
        return context_data

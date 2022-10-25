from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
)

from tapir.accounts.models import TapirUser
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.forms import (
    ShiftExemptionForm,
)
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftUserData,
    ShiftExemption,
    CreateExemptionLogEntry,
    UpdateExemptionLogEntry,
)


class CreateShiftExemptionView(PermissionRequiredMixin, TapirFormMixin, CreateView):
    model = ShiftExemption
    form_class = ShiftExemptionForm
    permission_required = PERMISSION_SHIFTS_MANAGE

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
            self.cancel_attendances_covered_by_exemption(exemption)
            CreateExemptionLogEntry().populate(
                start_date=exemption.start_date,
                end_date=exemption.end_date,
                actor=self.request.user,
                tapir_user=exemption.shift_user_data.user,
            ).save()
            return super().form_valid(form)

    @staticmethod
    def cancel_attendances_covered_by_exemption(exemption: ShiftExemption):
        user = exemption.shift_user_data.user
        for attendance in ShiftExemption.get_attendances_cancelled_by_exemption(
            user=user,
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
            ShiftAttendanceTemplate.objects.filter(user=user).delete()

    def get_success_url(self):
        return self.get_target_user_data().user.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tapir_user = self.get_target_user_data().user
        context["page_title"] = _("Shift exemption: %(name)s") % {
            "name": tapir_user.get_display_name()
        }
        context["card_title"] = _("Create shift exemption for: %(link)s") % {
            "link": tapir_user.get_html_link()
        }
        return context


class EditShiftExemptionView(
    PermissionRequiredMixin, TapirFormMixin, UpdateViewLogMixin, UpdateView
):
    model = ShiftExemption
    form_class = ShiftExemptionForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_success_url(self):
        return reverse("shifts:shift_exemption_list")

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            exemption: ShiftExemption = form.instance
            CreateShiftExemptionView.cancel_attendances_covered_by_exemption(exemption)

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
            "name": tapir_user.get_display_name()
        }
        context["card_title"] = _("Edit shift exemption for: %(link)s") % {
            "link": tapir_user.get_html_link()
        }
        return context


class ShiftExemptionListView(PermissionRequiredMixin, ListView):
    permission_required = [PERMISSION_SHIFTS_MANAGE]
    model = ShiftExemption

    def get_queryset(self):
        queryset = super().get_queryset()
        shift_user_data_id = self.request.GET.get("shift_user_data_id", None)
        if shift_user_data_id is not None:
            queryset = queryset.filter(shift_user_data__id=shift_user_data_id)
        return queryset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        shift_user_data_id = self.request.GET.get("shift_user_data_id", None)
        if shift_user_data_id is not None:
            context_data["shift_user_data"] = ShiftUserData.objects.get(
                pk=shift_user_data_id
            )
        return context_data

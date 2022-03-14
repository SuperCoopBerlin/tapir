from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
)

from tapir.shifts.forms import (
    ShiftExemptionForm,
)
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftUserData,
    ShiftExemption,
)


class CreateShiftExemptionView(PermissionRequiredMixin, CreateView):
    model = ShiftExemption
    form_class = ShiftExemptionForm
    permission_required = "shifts.manage"

    def get_target_user_data(self) -> ShiftUserData:
        return ShiftUserData.objects.get(pk=self.kwargs["shift_user_data_pk"])

    def get_form_kwargs(self, *args, **kwargs):
        self.object = self.model()
        self.object.shift_user_data = self.get_target_user_data()
        # Will pass the object to the form
        return super().get_form_kwargs(*args, **kwargs)

    def form_valid(self, form):
        exemption: ShiftExemption = form.instance
        user = self.get_target_user_data().user
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

        return super().form_valid(form)

    def get_success_url(self):
        return self.get_target_user_data().user.get_absolute_url()


class EditShiftExemptionView(PermissionRequiredMixin, UpdateView):
    model = ShiftExemption
    form_class = ShiftExemptionForm
    permission_required = "shifts.manage"

    def get_success_url(self):
        return reverse("shifts:shift_exemption_list")


class ShiftExemptionListView(PermissionRequiredMixin, ListView):
    permission_required = ["shifts.manage"]
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

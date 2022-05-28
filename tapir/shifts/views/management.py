from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import CreateView, TemplateView, UpdateView

from tapir.shifts.forms import ShiftCreateForm, ShiftSlotForm
from tapir.shifts.models import Shift, ShiftSlot


class ShiftManagementView(PermissionRequiredMixin, TemplateView):
    permission_required = "shifts.manage"
    template_name = "shifts/shift_management.html"


class ShiftCreateView(PermissionRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftCreateForm
    permission_required = "shifts.manage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = f"Creating a shift"
        return context


class ShiftSlotCreateView(PermissionRequiredMixin, CreateView):
    model = ShiftSlot
    form_class = ShiftSlotForm
    permission_required = "shifts.manage"

    def get_shift(self):
        return Shift.objects.get(pk=self.kwargs.get("shift_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "shift_name"
        ] = f"Adding a slot to {self.get_shift().get_display_name()}"
        return context

    def form_valid(self, form):
        form.instance.shift = self.get_shift()
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_shift().get_absolute_url()


class ShiftSlotEditView(PermissionRequiredMixin, UpdateView):
    model = ShiftSlot
    form_class = ShiftSlotForm
    permission_required = "shifts.manage"

    def get_success_url(self):
        return self.object.shift.get_absolute_url()

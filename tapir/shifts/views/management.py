import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.management import call_command
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    RedirectView,
    FormView,
    TemplateView,
)

from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.forms import (
    ShiftCreateForm,
    ShiftSlotForm,
    ShiftCancelForm,
    ShiftTemplateForm,
    ShiftSlotTemplateForm,
    ShiftDeleteForm,
    BulkShiftCancelForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftSlot,
    ShiftAttendance,
    ShiftTemplate,
    ShiftSlotTemplate,
)
from tapir.shifts.services.shift_cancellation_service import ShiftCancellationService


class ShiftCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftCreateForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Create a shift")
        return context


class ShiftSlotCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ShiftSlot
    form_class = ShiftSlotForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_shift(self):
        return Shift.objects.get(pk=self.kwargs.get("shift_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = (
            f"Adding a slot to {self.get_shift().get_display_name()}"
        )
        return context

    def form_valid(self, form):
        form.instance.shift = self.get_shift()
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_shift().get_absolute_url()


class ShiftSlotEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ShiftSlot
    form_class = ShiftSlotForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_success_url(self):
        return self.object.shift.get_absolute_url()

    def get_slot(self) -> ShiftSlot:
        return get_object_or_404(ShiftSlot, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Edit slot: ") + self.get_slot().get_display_name()
        return context


class CancelShiftView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = Shift
    form_class = ShiftCancelForm
    template_name = "shifts/cancel_shift.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        shift: Shift = form.instance
        ShiftCancellationService.cancel(shift)
        return response


class CancelDayShiftsView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = PERMISSION_SHIFTS_MANAGE
    form_class = BulkShiftCancelForm
    template_name = "shifts/shift_day_cancel.html"
    success_url = "/shifts/calendar"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        day = datetime.datetime.strptime(self.kwargs["day"], "%d-%m-%y").date()
        kwargs["shifts"] = Shift.objects.filter(start_time__date=day).order_by(
            "start_time"
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        day = datetime.datetime.strptime(self.kwargs["day"], "%d-%m-%y").date()
        context["day"] = day

        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            cancellation_reason = form.cleaned_data["cancellation_reason"]
            shift_ids_to_cancel = [
                k.split("_", maxsplit=1)[-1]
                for k, v in form.cleaned_data.items()
                if k.startswith("shift") and v is True
            ]
            print(shift_ids_to_cancel)
            for shift_id in shift_ids_to_cancel:
                shift = Shift.objects.get(pk=shift_id)
                shift.cancelled_reason = cancellation_reason
                ShiftCancellationService.cancel(shift)
            return response


class EditShiftView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = Shift
    form_class = ShiftCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Edit shift: ") + self.object.get_display_name()
        return context


class DeleteShiftView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = Shift
    form_class = ShiftDeleteForm
    template_name = "shifts/shift_confirm_delete.html"

    def get_shift(self):
        return get_object_or_404(Shift, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        context_data["shift"] = self.get_shift()
        return context_data

    def get_success_url(self):
        return reverse("shifts:calendar")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["shift"] = self.get_shift()
        return kwargs

    def form_valid(self, form):
        shift = self.get_shift()
        shift.deleted = True
        shift.save()
        return super().form_valid(form)


class EditShiftTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, UpdateView
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = ShiftTemplate
    form_class = ShiftTemplateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = (
            _("Edit shift template: ") + self.object.get_display_name()
        )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object.update_future_generated_shifts_to_fit_this()
        return super().form_valid(form)


class ShiftTemplateCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = ShiftTemplate
    form_class = ShiftTemplateForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Create an ABCD shift")
        context["help_text"] = _(
            "Shifts are generated every day at midnight. After you created the ABCD shift, come back tomorrow to see your shifts!"
        )
        return context


class ShiftSlotTemplateCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = ShiftSlotTemplate
    form_class = ShiftSlotTemplateForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_shift_template(self):
        return ShiftTemplate.objects.get(pk=self.kwargs.get("shift_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = (
            f"Adding a slot to {self.get_shift_template().get_display_name()}"
        )
        return context

    def form_valid(self, form):
        shift_template = self.get_shift_template()
        form.instance.shift_template = shift_template
        result = super().form_valid(form)
        for shift in shift_template.get_future_generated_shifts():
            form.instance.create_slot_from_template(shift)
        return result

    def get_success_url(self):
        return self.get_shift_template().get_absolute_url()


class ShiftSlotTemplateEditView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, UpdateView
):
    model = ShiftSlotTemplate
    form_class = ShiftSlotTemplateForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_slot_template(self):
        return ShiftSlotTemplate.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = f"Editing {self.get_slot_template().get_display_name()}"
        return context

    def form_valid(self, form):
        result = super().form_valid(form)
        for slot in self.get_slot_template().generated_slots.filter(
            shift__start_time__gt=timezone.now()
        ):
            slot.update_slot_from_template()
        return result

    def get_success_url(self):
        return self.get_slot_template().shift_template.get_absolute_url()


class GenerateShiftsManuallyView(
    LoginRequiredMixin, PermissionRequiredMixin, RedirectView
):
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_redirect_url(self, *args, **kwargs):
        return reverse("shifts:shift_management")

    def get(self, request, *args, **kwargs):
        call_command("generate_shifts")
        messages.info(request, _("Shifts generated."))
        return super().get(request, args, kwargs)

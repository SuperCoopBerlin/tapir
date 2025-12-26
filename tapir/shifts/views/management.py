import datetime
from itertools import product

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.management import call_command
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    RedirectView,
    FormView,
)

from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.forms import (
    ShiftCreateForm,
    ShiftSlotForm,
    ShiftCancelForm,
    ShiftTemplateForm,
    ShiftSlotTemplateForm,
    ShiftTemplateDuplicateForm,
    ShiftTemplateGroup,
    ShiftDeleteForm,
    BulkShiftCancelForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftSlot,
    ShiftTemplate,
    ShiftSlotTemplate,
)
from tapir.shifts.services.shift_cancellation_service import ShiftCancellationService
from tapir.shifts.services.shift_generator import ShiftGenerator
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator


class ShiftCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftCreateForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Create a shift")
        return context

    def form_valid(self, form):
        shift = form.save()

        ShiftWatchCreator.create_shift_watch_entries(shift=shift)

        return super().form_valid(form)


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
        kwargs["shifts"] = Shift.objects.filter(
            start_time__date=day, deleted=False
        ).order_by("start_time")
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
                form_field_key.split("_", maxsplit=1)[-1]
                for form_field_key, should_be_cancelled in form.cleaned_data.items()
                if form_field_key.startswith("shift") and should_be_cancelled
            ]
            for shift in Shift.objects.filter(id__in=shift_ids_to_cancel):
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


class ShiftTemplateDuplicateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, FormView
):
    form_class = ShiftTemplateDuplicateForm
    permission_required = PERMISSION_SHIFTS_MANAGE
    success_url = reverse_lazy("shifts:shift_template_overview")

    def get_context_data(self, **kwargs):
        template: ShiftTemplate = ShiftTemplate.objects.get(
            pk=self.kwargs.get("shift_pk")
        )
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Duplicate ABCD-Shift " + template.get_display_name())
        help_text = _(
            "Please choose the weekdays and ABCD-weeks this ABCD-Shift should be copied to. These slots will be copied: "
            + f"{", ".join(str(i) for i in template.slot_templates.values_list("name", flat=True).distinct())}."
        )
        if template.start_date is not None:
            help_text += _(
                " Shifts for this ABCD shift will be generated starting from "
                + template.start_date.strftime("%d.%m.%Y")
            )
        context["help_text"] = help_text
        return context

    def form_valid(self, form):
        shift_template_copy_source = ShiftTemplate.objects.get(
            pk=self.kwargs.get("shift_pk")
        )
        slot_templates_source = list(shift_template_copy_source.slot_templates.all())
        week_groups_by_id = {
            group.id: group for group in ShiftTemplateGroup.objects.all()
        }
        created_shift_template_ids = set()
        for weekday_as_string, week_group_id_as_string in product(
            form.cleaned_data["weekdays"], form.cleaned_data["week_group"]
        ):
            weekday = int(weekday_as_string)
            week_group_id = int(week_group_id_as_string)

            if (
                weekday == shift_template_copy_source.weekday
                and week_group_id == shift_template_copy_source.group.id
            ):
                continue

            created_shift_template_id = self.create_copy(
                shift_template_source=shift_template_copy_source,
                slot_templates_source=slot_templates_source,
                weekday=weekday,
                group=week_groups_by_id[week_group_id],
            )
            created_shift_template_ids.add(created_shift_template_id)

        ShiftGenerator.generate_shifts_up_to(
            filter_group_ids={
                int(group_id_as_string)
                for group_id_as_string in form.cleaned_data["week_group"]
            },
            filter_shift_template_ids=created_shift_template_ids,
        )

        return super().form_valid(form)

    @classmethod
    def create_copy(
        cls,
        shift_template_source: ShiftTemplate,
        slot_templates_source: list[ShiftSlotTemplate],
        weekday: int,
        group: ShiftTemplateGroup,
    ) -> int:

        shift_template_copy_destination = ShiftTemplate.objects.create(
            name=shift_template_source.name,
            description=shift_template_source.description,
            flexible_time=shift_template_source.flexible_time,
            group=group,
            num_required_attendances=shift_template_source.num_required_attendances,
            weekday=weekday,
            start_time=shift_template_source.start_time,
            end_time=shift_template_source.end_time,
            start_date=shift_template_source.start_date,
        )

        slot_templates_to_create = [
            ShiftSlotTemplate(
                shift_template=shift_template_copy_destination,
                name=slot_template.name,
                required_capabilities=slot_template.required_capabilities,
                warnings=slot_template.warnings,
            )
            for slot_template in slot_templates_source
        ]
        ShiftSlotTemplate.objects.bulk_create(slot_templates_to_create)

        return shift_template_copy_destination.id


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

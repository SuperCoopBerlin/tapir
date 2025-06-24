from django.conf import settings
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
)
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.forms import (
    ShiftCreateForm,
    ShiftSlotForm,
    ShiftCancelForm,
    ShiftTemplateForm,
    ShiftSlotTemplateForm,
    ShiftDeleteForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftSlot,
    ShiftAttendance,
    ShiftTemplate,
    ShiftSlotTemplate,
    ShiftSlotWarning,
    ShiftSlotWarningTranslation,
    ShiftUserCapability,
    ShiftUserCapabilityTranslation,
)
from tapir.shifts.serializers import (
    ShiftSlotWarningSerializer,
    CreateShiftSlotWarningRequestSerializer,
    UpdateShiftSlotWarningRequestSerializer,
    LanguageSerializer,
    CreateShiftUserCapabilityRequestSerializer,
    UpdateShiftUserCapabilityRequestSerializer,
    ShiftUserCapabilitySerializer,
)
from tapir.utils.models import PREFERRED_LANGUAGES


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
        with transaction.atomic():
            response = super().form_valid(form)

            shift: Shift = form.instance
            shift.cancelled = True
            shift.save()

            for slot in shift.slots.all():
                attendance = slot.get_valid_attendance()
                if not attendance:
                    continue
                if (
                    hasattr(slot.slot_template, "attendance_template")
                    and slot.slot_template.attendance_template.user == attendance.user
                ):
                    attendance.state = ShiftAttendance.State.MISSED_EXCUSED
                    attendance.excused_reason = "Shift cancelled"
                    attendance.save()
                    attendance.update_shift_account_entry()
                else:
                    attendance.state = ShiftAttendance.State.CANCELLED
                    attendance.save()

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


class ShiftSlotWarningViewSet(PermissionRequiredMixin, ReadOnlyModelViewSet):
    permission_required = PERMISSION_SHIFTS_MANAGE
    queryset = ShiftSlotWarning.objects.all()
    serializer_class = ShiftSlotWarningSerializer


class ShiftSlotWarningApiView(PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_SHIFTS_MANAGE

    @extend_schema(
        responses={200: int}, request=CreateShiftSlotWarningRequestSerializer
    )
    def post(self, request):
        serializer = CreateShiftSlotWarningRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            warning = ShiftSlotWarning.objects.create()
            translations = [
                ShiftSlotWarningTranslation(
                    warning=warning, language=language, name=name, description=""
                )
                for language, name in serializer.validated_data["translations"].items()
            ]
            ShiftSlotWarningTranslation.objects.bulk_create(translations)

        return Response(warning.id)

    @extend_schema(
        responses={200: str}, request=UpdateShiftSlotWarningRequestSerializer
    )
    def patch(self, request):
        serializer = UpdateShiftSlotWarningRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warning = get_object_or_404(
            ShiftSlotWarning, id=serializer.validated_data["id"]
        )
        warning.shiftslotwarningtranslation_set.all().delete()

        with transaction.atomic():
            translations = [
                ShiftSlotWarningTranslation(
                    warning=warning, language=language, name=name, description=""
                )
                for language, name in serializer.validated_data["translations"].items()
            ]
            ShiftSlotWarningTranslation.objects.bulk_create(translations)

        return Response("OK")

    @extend_schema(
        responses={200: str},
        parameters=[OpenApiParameter(name="id", required=True, type=int)],
    )
    def delete(self, request):
        warning = get_object_or_404(ShiftSlotWarning, id=request.query_params.get("id"))
        warning.delete()
        return Response("OK")


class GetLanguagesView(PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_SHIFTS_MANAGE

    @extend_schema(responses={200: LanguageSerializer(many=True)})
    def get(self, request):
        german = PREFERRED_LANGUAGES[0]
        english = PREFERRED_LANGUAGES[1]
        portuguese = PREFERRED_LANGUAGES[2]

        if settings.ENABLE_RIZOMA_CONTENT:
            languages = [english, portuguese]
        else:
            languages = [english, german]

        return Response(
            LanguageSerializer(
                [
                    {"short_name": language[0], "display_name": language[1]}
                    for language in languages
                ],
                many=True,
            ).data
        )


class ShiftUserCapabilityViewSet(PermissionRequiredMixin, ReadOnlyModelViewSet):
    permission_required = PERMISSION_SHIFTS_MANAGE
    queryset = ShiftUserCapability.objects.all()
    serializer_class = ShiftUserCapabilitySerializer


class ShiftUserCapabilityApiView(PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_SHIFTS_MANAGE

    @extend_schema(
        responses={200: int}, request=CreateShiftUserCapabilityRequestSerializer
    )
    def post(self, request):
        serializer = CreateShiftUserCapabilityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            capability = ShiftUserCapability.objects.create()
            translations = [
                ShiftUserCapabilityTranslation(
                    capability=capability,
                    language=language,
                    name=name,
                    description="",
                )
                for language, name in serializer.validated_data["translations"].items()
            ]
            ShiftUserCapabilityTranslation.objects.bulk_create(translations)

        return Response(capability.id)

    @extend_schema(
        responses={200: str}, request=UpdateShiftUserCapabilityRequestSerializer
    )
    def patch(self, request):
        serializer = UpdateShiftUserCapabilityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        capability = get_object_or_404(
            ShiftUserCapability, id=serializer.validated_data["id"]
        )
        capability.shiftusercapabilitytranslation_set.all().delete()

        with transaction.atomic():
            translations = [
                ShiftUserCapabilityTranslation(
                    capability=capability,
                    language=language,
                    name=name,
                    description="",
                )
                for language, name in serializer.validated_data["translations"].items()
            ]
            ShiftUserCapabilityTranslation.objects.bulk_create(translations)

        return Response("OK")

    @extend_schema(
        responses={200: str},
        parameters=[OpenApiParameter(name="id", required=True, type=int)],
    )
    def delete(self, request):
        capability = get_object_or_404(
            ShiftUserCapability, id=request.query_params.get("id")
        )
        capability.delete()
        return Response("OK")

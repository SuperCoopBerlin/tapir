from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    UpdateView,
    FormView,
)

from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.emails.shift_missed_email import ShiftMissedEmail
from tapir.shifts.emails.stand_in_found_email import StandInFoundEmail
from tapir.shifts.forms import (
    ShiftAttendanceTemplateForm,
    UpdateShiftAttendanceForm,
    RegisterUserToShiftSlotForm,
)
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftSlot,
    ShiftSlotTemplate,
    CreateShiftAttendanceTemplateLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
    CreateShiftAttendanceLogEntry,
    UpdateShiftAttendanceStateLogEntry,
    ShiftAttendanceTakenOverLogEntry,
)
from tapir.shifts.views.views import SelectedUserViewMixin
from tapir.utils.shortcuts import safe_redirect
from tapir.utils.user_utils import UserUtils


class RegisterUserToShiftSlotTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, SelectedUserViewMixin, CreateView
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = ShiftAttendanceTemplate
    template_name = "shifts/register_user_to_shift_slot_template.html"
    form_class = ShiftAttendanceTemplateForm

    def get_initial(self):
        return {"user": self.get_selected_user()}

    def get_slot_template(self):
        return get_object_or_404(ShiftSlotTemplate, pk=self.kwargs["slot_template_pk"])

    def get_context_data(self, **kwargs):
        slot_template = self.get_slot_template()
        kwargs["slot_template"] = slot_template

        blocked_slots = []
        for slot in slot_template.generated_slots.filter(
            shift__start_time__gte=timezone.now()
        ):
            attendance = slot.get_valid_attendance()
            if attendance is not None:
                blocked_slots.append(slot)
        kwargs["blocked_slots"] = blocked_slots

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.instance.slot_template = self.get_slot_template()
        with transaction.atomic():
            response = super().form_valid(form)

            shift_attendance_template: ShiftAttendanceTemplate = self.object

            for (
                shift
            ) in shift_attendance_template.slot_template.shift_template.generated_shifts.filter(
                start_time__gt=timezone.now()
            ):
                # Check for future cancelled shifts, the user should get a point.
                attendance = ShiftAttendance.objects.filter(
                    user=shift_attendance_template.user, slot__shift=shift
                ).first()
                if not shift.cancelled or not attendance:
                    continue
                attendance.state = ShiftAttendance.State.MISSED_EXCUSED
                attendance.save()
                attendance.update_shift_account_entry(shift.cancelled_reason)

            CreateShiftAttendanceTemplateLogEntry().populate(
                actor=self.request.user,
                tapir_user=self.object.user,
                shift_attendance_template=shift_attendance_template,
            ).save()

        return response

    def get_success_url(self):
        if self.get_selected_user():
            return self.get_selected_user().get_absolute_url()
        return self.object.slot_template.shift_template.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"slot_template_pk": self.kwargs["slot_template_pk"]})
        return kwargs


class UpdateShiftAttendanceStateBase(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = ShiftAttendance
    get_state_from_kwargs = True

    def get_attendance(self):
        return ShiftAttendance.objects.get(pk=self.kwargs["pk"])

    def get_permission_required(self):
        state = self.kwargs["state"]
        self_unregister = (
            state == ShiftAttendance.State.CANCELLED
            and self.get_attendance().slot.user_can_self_unregister(self.request.user)
        )
        look_for_standing = (
            state == ShiftAttendance.State.LOOKING_FOR_STAND_IN
            and self.get_attendance().slot.user_can_look_for_standin(self.request.user)
        )
        cancel_look_for_standing = (
            state == ShiftAttendance.State.PENDING
            and self.get_attendance().state
            == ShiftAttendance.State.LOOKING_FOR_STAND_IN
        )
        if self_unregister or look_for_standing or cancel_look_for_standing:
            return []
        return [PERMISSION_SHIFTS_MANAGE]

    def get_success_url(self):
        return self.get_object().slot.shift.get_absolute_url()

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            attendance = self.get_attendance()
            if self.get_state_from_kwargs:
                attendance.state = self.kwargs["state"]
                attendance.save()

            UpdateShiftAttendanceStateLogEntry().populate(
                actor=self.request.user,
                tapir_user=attendance.user,
                attendance=attendance,
            ).save()

            if attendance.state == ShiftAttendance.State.MISSED:
                attendance = self.get_attendance()
                mail = ShiftMissedEmail(shift=attendance.slot.shift)
                mail.send_to_tapir_user(
                    actor=self.request.user, recipient=attendance.user
                )

            description = None
            if "description" in form.data:
                description = form.data["description"]
            attendance.update_shift_account_entry(description)

            return response


class UpdateShiftAttendanceStateView(UpdateShiftAttendanceStateBase):
    fields = []


class UpdateShiftAttendanceStateWithFormView(
    TapirFormMixin, UpdateShiftAttendanceStateBase
):
    form_class = UpdateShiftAttendanceForm
    get_state_from_kwargs = False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"state": self.kwargs["state"]})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        attendance: ShiftAttendance = self.object
        context["page_title"] = _("Shift attendance: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                attendance.user, self.request.user
            )
        }
        context["card_title"] = _(
            "Updating shift attendance: %(member_link)s, %(slot_link)s"
            % {
                "member_link": UserUtils.build_html_link_for_viewer(
                    attendance.user, self.request.user
                ),
                "slot_link": attendance.slot.get_html_link(),
            }
        )
        return context


@require_POST
@csrf_protect
@login_required
@permission_required(PERMISSION_SHIFTS_MANAGE)
def shift_attendance_template_delete(request, pk):
    shift_attendance_template = get_object_or_404(ShiftAttendanceTemplate, pk=pk)
    slot_template = shift_attendance_template.slot_template

    with transaction.atomic():
        DeleteShiftAttendanceTemplateLogEntry().populate(
            actor=request.user,
            tapir_user=shift_attendance_template.user,
            shift_attendance_template=shift_attendance_template,
        ).save()

        shift_attendance_template.cancel_attendances(timezone.now())
        shift_attendance_template.delete()

    return safe_redirect(request.GET.get("next"), slot_template.shift_template, request)


class RegisterUserToShiftSlotView(
    LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    template_name = "shifts/register_user_to_shift_slot.html"
    form_class = RegisterUserToShiftSlotForm

    def get_permission_required(self):
        if self.get_slot().user_can_attend(self.request.user):
            return []
        return [PERMISSION_SHIFTS_MANAGE]

    def get_slot(self) -> ShiftSlot:
        return get_object_or_404(ShiftSlot, pk=self.kwargs["slot_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "slot": self.get_slot(),
                "request_user": self.request.user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["slot"] = self.get_slot()
        return context

    def get_initial(self):
        if self.request.user.has_perm(PERMISSION_SHIFTS_MANAGE):
            return {}
        return {"user": self.request.user}

    def get_success_url(self):
        return self.get_slot().shift.get_absolute_url()

    @staticmethod
    def mark_stand_in_found_if_relevant(slot: ShiftSlot, actor: User):
        attendances = ShiftAttendance.objects.filter(
            slot=slot, state=ShiftAttendance.State.LOOKING_FOR_STAND_IN
        )
        if not attendances.exists():
            return

        attendance = attendances.first()
        attendance.state = ShiftAttendance.State.CANCELLED
        attendance.save()

        ShiftAttendanceTakenOverLogEntry().populate(
            actor=actor, tapir_user=attendance.user, attendance=attendance
        ).save()

        email = StandInFoundEmail(attendance.slot.shift)
        email.send_to_tapir_user(actor=actor, recipient=attendance.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        slot = self.get_slot()
        user_to_register = form.cleaned_data["user"]

        with transaction.atomic():
            attendance = ShiftAttendance.objects.create(
                user=user_to_register, slot=slot
            )
            self.mark_stand_in_found_if_relevant(slot, self.request.user)
            CreateShiftAttendanceLogEntry().populate(
                actor=self.request.user,
                tapir_user=user_to_register,
                attendance=attendance,
            ).save()

        return response

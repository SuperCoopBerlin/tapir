from datetime import datetime

import django_tables2
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.template.defaulttags import register
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    UpdateView,
)
from django.views.generic import DetailView, TemplateView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.shifts.forms import (
    ShiftUserDataForm,
    CreateShiftAccountEntryForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    SHIFT_ATTENDANCE_STATES,
    ShiftTemplate,
)
from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendanceMode,
    UpdateShiftUserDataLogEntry,
    ShiftUserData,
    ShiftAccountEntry,
)
from tapir.shifts.templatetags.shifts import shift_name_as_class


class SelectedUserViewMixin:
    """Mixin to allow passing a selected_user GET param to a view.

    This is useful to use a view in a for-somebody-else context, e.g. when going there
    from a user page. Often, this user will be passed on to a following view or modify
    the behavior of the view."""

    def get_selected_user(self):
        if "selected_user" in self.request.GET:
            return get_object_or_404(TapirUser, pk=self.request.GET["selected_user"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_user"] = self.get_selected_user()
        return context


class EditShiftUserDataView(PermissionRequiredMixin, UpdateViewLogMixin, UpdateView):
    permission_required = "shifts.manage"
    model = ShiftUserData
    form_class = ShiftUserDataForm

    def get_success_url(self):
        return self.object.user.get_absolute_url()

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                log_entry = UpdateShiftUserDataLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    user=self.object.user,
                    actor=self.request.user,
                )
                log_entry.save()

            return response


def get_shift_slot_names():
    shift_slot_names = (
        ShiftSlot.objects.filter(shift__start_time__gt=timezone.now())
        .values_list("name", flat=True)
        .distinct()
    )
    shift_slot_names = [
        (shift_name_as_class(name), _(name)) for name in shift_slot_names if name != ""
    ]
    shift_slot_names.append(("", _("General")))
    return shift_slot_names


@register.filter
def dictionary_get(dic, key):
    return dic[key] if key in dic else None


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def set_user_attendance_mode_flying(request, user_pk):
    return _set_user_attendance_mode(request, user_pk, ShiftAttendanceMode.FLYING)


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def set_user_attendance_mode_regular(request, user_pk):
    return _set_user_attendance_mode(request, user_pk, ShiftAttendanceMode.REGULAR)


def _set_user_attendance_mode(request, user_pk, attendance_mode):
    user = get_object_or_404(TapirUser, pk=user_pk)
    old_shift_user_data = freeze_for_log(user.shift_user_data)

    with transaction.atomic():
        user.shift_user_data.attendance_mode = attendance_mode
        user.shift_user_data.save()
        log_entry = UpdateShiftUserDataLogEntry().populate(
            actor=request.user,
            user=user,
            old_frozen=old_shift_user_data,
            new_model=user.shift_user_data,
        )
        log_entry.save()

    return redirect(user)


class UserShiftAccountLog(PermissionRequiredMixin, TemplateView):
    template_name = "shifts/user_shift_account_log.html"

    def get_target_user(self):
        return TapirUser.objects.get(pk=self.kwargs["user_pk"])

    def get_permission_required(self):
        if self.request.user == self.get_target_user():
            return []
        return ["shifts.manage"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["user"] = self.get_target_user()
        context["entries"] = ShiftAccountEntry.objects.filter(
            user=self.get_target_user()
        ).order_by("-date")
        return context


class CreateShiftAccountEntryView(PermissionRequiredMixin, CreateView):
    model = ShiftAccountEntry
    form_class = CreateShiftAccountEntryForm
    permission_required = "shifts.manage"

    def get_target_user(self) -> TapirUser:
        return TapirUser.objects.get(pk=self.kwargs["user_pk"])

    def form_valid(self, form):
        form.instance.user = self.get_target_user()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["user"] = self.get_target_user()
        return context

    def get_success_url(self):
        return self.get_target_user().get_absolute_url()


class ShiftDetailView(LoginRequiredMixin, DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift: Shift = context["shift"]
        slots = shift.slots.all()

        for slot in slots:
            slot.is_occupied = ShiftAttendance.objects.filter(
                slot=slot,
                state__in=[ShiftAttendance.State.PENDING, ShiftAttendance.State.DONE],
            ).exists()
            slot.can_self_register = slot.user_can_attend(self.request.user)
            slot.can_self_unregister = slot.user_can_self_unregister(self.request.user)
            slot.can_look_for_stand_in = slot.user_can_look_for_standin(
                self.request.user
            )

            slot.previous_attendances = ShiftAttendance.objects.filter(slot=slot)
            if slot.get_valid_attendance() is not None:
                slot.previous_attendances = slot.previous_attendances.exclude(
                    id=slot.get_valid_attendance().id
                )

        context["slots"] = slots
        context["attendance_states"] = ShiftAttendance.State
        context["NB_DAYS_FOR_SELF_UNREGISTER"] = Shift.NB_DAYS_FOR_SELF_UNREGISTER
        context[
            "NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN"
        ] = Shift.NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN
        context["SHIFT_ATTENDANCE_STATES"] = SHIFT_ATTENDANCE_STATES
        return context


class ShiftDayPrintableView(PermissionRequiredMixin, TemplateView):
    template_name = "shifts/shift_day_printable.html"
    permission_required = "shifts.manage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        day = datetime.strptime(kwargs["day"], "%d-%m-%y").date()
        context["shifts"] = Shift.objects.filter(start_time__date=day)
        return context


class ShiftTemplateDetail(LoginRequiredMixin, SelectedUserViewMixin, DetailView):
    template_name = "shifts/shift_template_detail.html"
    model = ShiftTemplate


class ShiftUserDataTable(django_tables2.Table):
    class Meta:
        model = ShiftUserData
        template_name = "django_tables2/bootstrap4.html"
        fields = [
            "account_balance",
            "attendance_mode",
        ]
        sequence = (
            "display_name",
            "account_balance",
            "attendance_mode",
        )
        order_by = "account_balance"

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )
    email = django_tables2.Column(empty_values=(), orderable=False, visible=False)

    def render_display_name(self, value, record: ShiftUserData):
        return format_html(
            "<a href={}>{}</a>",
            record.user.get_absolute_url(),
            record.user.get_display_name(),
        )

    def value_display_name(self, value, record: ShiftUserData):
        return record.user.get_display_name()

    def value_email(self, value, record: ShiftUserData):
        return record.user.email


class MembersOnAlertView(PermissionRequiredMixin, ExportMixin, SingleTableView):
    table_class = ShiftUserDataTable
    model = ShiftUserData
    template_name = "shifts/members_on_alert_list.html"
    permission_required = "coop.manage"

    export_formats = ["csv", "json"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("user")
            .annotate(account_balance=Sum("user__shift_account_entries__value"))
            .filter(account_balance__lt=-1)
            .order_by("user__date_joined")
        )

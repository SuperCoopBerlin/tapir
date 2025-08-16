import datetime

import django_tables2
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.management import call_command
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.template.defaulttags import register
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic import (
    CreateView,
    UpdateView,
    RedirectView,
    FormView,
)
from django.views.generic import DetailView, TemplateView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.core.config import (
    TAPIR_TABLE_CLASSES,
    TAPIR_TABLE_TEMPLATE,
)
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_COOP_MANAGE,
    PERMISSION_SHIFTS_MANAGE,
    PERMISSION_WELCOMEDESK_VIEW,
)
from tapir.shifts.forms import (
    ShiftUserDataForm,
    CreateShiftAccountEntryForm,
    ShiftWatchForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    SHIFT_ATTENDANCE_STATES,
    ShiftTemplate,
    ShiftWatch,
)
from tapir.shifts.models import (
    ShiftSlot,
    UpdateShiftUserDataLogEntry,
    ShiftUserData,
    ShiftAccountEntry,
)
from tapir.shifts.templatetags.shifts import shift_name_as_class
from tapir.utils.user_utils import UserUtils


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


class EditShiftUserDataView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateViewLogMixin,
    TapirFormMixin,
    UpdateView,
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = ShiftUserData
    form_class = ShiftUserDataForm

    def get_initial(self):
        shift_user_data: ShiftUserData = self.get_object()
        return {
            "shift_partner": (
                shift_user_data.shift_partner.user.id
                if shift_user_data.shift_partner
                else None
            )
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request_user": self.request.user})
        return kwargs

    def get_success_url(self):
        return self.object.user.get_absolute_url()

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)

        tapir_user = form.cleaned_data["shift_partner"]
        form.instance.shift_partner = tapir_user.shift_user_data if tapir_user else None
        form.instance.save()

        new_frozen = freeze_for_log(form.instance)
        if self.old_object_frozen != new_frozen:
            UpdateShiftUserDataLogEntry().populate(
                old_frozen=self.old_object_frozen,
                new_frozen=new_frozen,
                tapir_user=self.object.user,
                actor=self.request.user,
            ).save()

        return response

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        tapir_user: TapirUser = self.object.user
        context_data["page_title"] = _("Edit user shift data: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                tapir_user, self.request.user
            )
        }
        context_data["card_title"] = _("Edit user shift data: %(name)s") % {
            "name": UserUtils.build_html_link_for_viewer(tapir_user, self.request.user)
        }
        return context_data


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


class UserShiftAccountLog(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/user_shift_account_log.html"

    def get_target_user(self) -> TapirUser:
        return TapirUser.objects.get(pk=self.kwargs["user_pk"])

    def get_permission_required(self):
        if self.request.user == self.get_target_user():
            return []
        return [PERMISSION_SHIFTS_MANAGE]

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        user = self.get_target_user()
        context["user"] = user
        context["entries_data"] = [
            {
                "entry": entry,
                "balance_at_date": user.shift_user_data.get_account_balance(
                    at_date=entry.date
                ),
            }
            for entry in ShiftAccountEntry.objects.filter(user=user).order_by("-date")
        ]
        return context


class CreateShiftAccountEntryView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = ShiftAccountEntry
    form_class = CreateShiftAccountEntryForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_target_user(self) -> TapirUser:
        return TapirUser.objects.get(pk=self.kwargs["user_pk"])

    def form_valid(self, form):
        form.instance.user = self.get_target_user()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        tapir_user = self.get_target_user()
        context_data["page_title"] = _("Shift account: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                tapir_user, self.request.user
            )
        }
        context_data["card_title"] = _(
            "Create manual shift account entry for: %(link)s"
        ) % {
            "link": UserUtils.build_html_link_for_viewer(tapir_user, self.request.user)
        }
        return context_data

    def get_success_url(self):
        return self.get_target_user().get_absolute_url()


class ShiftDetailView(LoginRequiredMixin, DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift: Shift = context["shift"]
        slots = (
            shift.slots.all()
            .annotate(
                is_occupied=Count(
                    "attendances",
                    filter=Q(
                        attendances__state__in=[
                            ShiftAttendance.State.PENDING,
                            ShiftAttendance.State.DONE,
                        ]
                    ),
                )
            )
            .prefetch_related("slot_template__attendance_template__user")
        )

        for slot in slots:
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
        context["NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN"] = (
            Shift.NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN
        )
        context["SHIFT_ATTENDANCE_STATES"] = SHIFT_ATTENDANCE_STATES
        return context


class ShiftDayPrintableView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/shift_day_printable.html"
    permission_required = PERMISSION_WELCOMEDESK_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        day = datetime.datetime.strptime(kwargs["day"], "%d-%m-%y").date()
        context["shifts"] = Shift.objects.filter(start_time__date=day).order_by(
            "start_time"
        )
        return context


class ShiftTemplateDetail(LoginRequiredMixin, SelectedUserViewMixin, DetailView):
    template_name = "shifts/shift_template_detail.html"
    model = ShiftTemplate

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related(
            "slot_templates__attendance_template__user__share_owner"
        )


class ShiftUserDataTable(django_tables2.Table):
    class Meta:
        model = ShiftUserData
        template_name = TAPIR_TABLE_TEMPLATE
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
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )
    email = django_tables2.Column(empty_values=(), orderable=False, visible=False)

    def before_render(self, request):
        self.request = request

    def render_display_name(self, value, record: ShiftUserData):
        return UserUtils.build_html_link_for_viewer(record.user, self.request.user)

    def value_display_name(self, value, record: ShiftUserData):
        return UserUtils.build_display_name_for_viewer(record.user, self.request.user)

    def value_email(self, value, record: ShiftUserData):
        return record.user.email


class MembersOnAlertView(
    LoginRequiredMixin, PermissionRequiredMixin, ExportMixin, SingleTableView
):
    table_class = ShiftUserDataTable
    model = ShiftUserData
    template_name = "shifts/members_on_alert_list.html"
    permission_required = PERMISSION_COOP_MANAGE

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


class ShiftManagementView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/shift_management.html"
    permission_required = PERMISSION_SHIFTS_MANAGE


class RunFreezeChecksManuallyView(
    LoginRequiredMixin, PermissionRequiredMixin, RedirectView
):
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_redirect_url(self, *args, **kwargs):
        return reverse("shifts:shift_management")

    def get(self, request, *args, **kwargs):
        call_command("run_freeze_checks")
        messages.info(request, _("Frozen statuses updated."))
        return super().get(request, args, kwargs)


# class WatchShiftView(LoginRequiredMixin, RedirectView):
#     def post(self, request, *args, **kwargs):
#         shift = get_object_or_404(Shift, pk=kwargs["shift_id"])
#         ShiftWatch.objects.get_or_create(user=request.user, shift=shift)
#         return redirect("shifts:shift_detail", pk=kwargs["shift_id"])
#


class UnwatchShiftView(LoginRequiredMixin, RedirectView):
    def post(self, request, *args, **kwargs):
        shift = get_object_or_404(Shift, id=kwargs["shift"])
        ShiftWatch.objects.filter(user=request.user, shift=shift).delete()
        return redirect("shifts:shift_detail", pk=kwargs["shift"])


class WatchShiftView(LoginRequiredMixin, TapirFormMixin, CreateView):
    model = ShiftWatch
    form_class = ShiftWatchForm

    def get_success_url(self):
        return reverse_lazy("shifts:shift_detail", args=[self.kwargs["shift"]])

    def form_valid(self, form):
        form.instance.shift = Shift.objects.get(id=self.kwargs["shift"])
        form.instance.user = self.request.user
        return super().form_valid(form)

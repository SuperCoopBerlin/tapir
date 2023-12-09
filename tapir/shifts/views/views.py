import datetime

import django_tables2
from chartjs.views import JSONView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.management import call_command
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.defaulttags import register
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    RedirectView,
)
from django.views.generic import DetailView, TemplateView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.core.config import (
    TAPIR_TABLE_CLASSES,
    TAPIR_TABLE_TEMPLATE,
    feature_flag_solidarity_shifts,
)
from tapir.core.models import FeatureFlag
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import PERMISSION_COOP_MANAGE, PERMISSION_SHIFTS_MANAGE
from tapir.shifts.forms import (
    ShiftUserDataForm,
    CreateShiftAccountEntryForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    SHIFT_ATTENDANCE_STATES,
    ShiftTemplate,
    SolidarityShift,
)
from tapir.shifts.models import (
    ShiftSlot,
    UpdateShiftUserDataLogEntry,
    ShiftUserData,
    ShiftAccountEntry,
)
from tapir.shifts.templatetags.shifts import shift_name_as_class
from tapir.utils.shortcuts import get_first_of_next_month
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

    def get_success_url(self):
        return self.object.user.get_absolute_url()

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

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
            "Create manual shift account entry for:  %(link)s"
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


class ShiftDayPrintableView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/shift_day_printable.html"
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        day = datetime.datetime.strptime(kwargs["day"], "%d-%m-%y").date()
        context["shifts"] = Shift.objects.filter(start_time__date=day)
        return context


class ShiftTemplateDetail(LoginRequiredMixin, SelectedUserViewMixin, DetailView):
    template_name = "shifts/shift_template_detail.html"
    model = ShiftTemplate


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


class SolidarityShiftUsed(LoginRequiredMixin, RedirectView):
    def post(self, request, *args, **kwargs):
        date = timezone.now()
        tapir_user = get_object_or_404(TapirUser, pk=kwargs["pk"])

        if not (
            request.user.pk == tapir_user.pk
            or request.user.has_perm(PERMISSION_SHIFTS_MANAGE)
        ):
            return HttpResponseForbidden(
                "You don't have permission to use Solidarity Shifts on behalf of another user."
            )
        elif not FeatureFlag.get_flag_value(feature_flag_solidarity_shifts):
            return HttpResponseBadRequest(
                "The Solidarity Shift feature is not enabled."
            )

        solidarity_shift = SolidarityShift.objects.filter(is_used_up=False)[0]

        if not solidarity_shift:
            return HttpResponseBadRequest("There are no available Solidarity Shifts")
        if tapir_user.shift_user_data.get_used_solidarity_shifts_current_year() >= 2:
            return HttpResponseBadRequest(
                "You already used 2 Solidarity Shifts this year"
            )

        solidarity_shift.is_used_up = True
        solidarity_shift.date_used = date
        solidarity_shift.save()

        ShiftAccountEntry(
            user=tapir_user,
            value=1,
            is_solidarity_used=True,
            date=date,
            description="Solidarity shift received",
        ).save()

        messages.info(
            request, _("Solidarity Shift received. Account Balance increased by 1.")
        )

        return redirect(tapir_user.get_absolute_url())


class SolidarityShiftGiven(LoginRequiredMixin, RedirectView):
    def post(self, request, *args, **kwargs):
        if not FeatureFlag.get_flag_value(feature_flag_solidarity_shifts):
            return HttpResponseBadRequest(
                "The Solidarity Shift feature is not enabled."
            )
        tapir_user = get_object_or_404(TapirUser, pk=kwargs["pk"])
        shift_attendance = tapir_user.shift_attendances.filter(
            is_solidarity=False, state=ShiftAttendance.State.DONE
        )[0]

        SolidarityShift.objects.create(shiftAttendance=shift_attendance)

        shift_attendance.is_solidarity = True
        shift_attendance.save()

        ShiftAccountEntry(
            user=tapir_user,
            value=-1,
            date=timezone.now(),
            description="Solidarity shift given",
            is_from_welcome_session=False,
        ).save()

        messages.info(
            request, _("Solidarity Shift given. Account Balance debited with -1.")
        )

        return redirect(tapir_user.get_absolute_url())


class SolidarityShiftsView(LoginRequiredMixin, TemplateView):
    template_name = "shifts/solidarity_shifts_overview.html"
    model = SolidarityShift

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_solidarity_shifts"] = SolidarityShift.objects.filter(
            is_used_up=False
        ).count()
        context["used_solidarity_shifts_total"] = SolidarityShift.objects.filter(
            is_used_up=True
        ).count()
        context["gifted_solidarity_shifts_total"] = SolidarityShift.objects.count()
        return context


class CacheDatesFirstSolidarityToTodayMixin:
    def __init__(self):
        super().__init__()

    def get_dates_from_first_solidarity_to_today(self):
        first_solidarity = SolidarityShift.objects.order_by("date_gifted").first()
        if not first_solidarity:
            return []

        current_date = first_solidarity.date_gifted.replace(day=1)
        end_date = datetime.date.today()
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        return dates


class GiftedSolidarityShiftsJsonView(CacheDatesFirstSolidarityToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        data = []
        dates = self.get_dates_from_first_solidarity_to_today()

        for date in dates:
            month_num = int(date.strftime("%m"))
            year = int(date.strftime("%Y"))
            data.append(
                SolidarityShift.objects.filter(
                    date_gifted__month=month_num, date_gifted__year=year
                ).count()
            )

        context_data = {
            "type": "bar",
            "data": {
                "labels": [date.strftime("%b %Y") for date in dates],
                "datasets": [
                    {
                        "label": _("Solidarity shifts gifted"),
                        "data": data,
                    }
                ],
            },
        }
        return context_data


class UsedSolidarityShiftsJsonView(CacheDatesFirstSolidarityToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        data = []
        dates = self.get_dates_from_first_solidarity_to_today()

        for date in dates:
            month_num = int(date.strftime("%m"))
            year = int(date.strftime("%Y"))
            data.append(
                SolidarityShift.objects.filter(
                    date_used__month=month_num, date_used__year=year
                ).count()
            )

        context_data = {
            "type": "bar",
            "data": {
                "labels": [date.strftime("%b %Y") for date in dates],
                "datasets": [
                    {
                        "label": _("Solidarity shifts used"),
                        "data": data,
                    }
                ],
            },
        }
        return context_data

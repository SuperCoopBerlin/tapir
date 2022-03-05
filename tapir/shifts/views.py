import datetime
from collections import OrderedDict
from datetime import date, time, timedelta

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    TemplateView,
    DetailView,
    CreateView,
    UpdateView,
    ListView,
)
from werkzeug.exceptions import BadRequest

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.log.util import freeze_for_log
from tapir.settings import FROM_EMAIL_MEMBER_OFFICE
from tapir.shifts.forms import (
    ShiftCreateForm,
    ShiftAttendanceTemplateForm,
    ShiftAttendanceForm,
    ShiftUserDataForm,
    CreateShiftAccountEntryForm,
    UpdateShiftAttendanceForm,
    ShiftExemptionForm,
)
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftTemplateGroup,
    ShiftAttendanceTemplate,
    ShiftSlot,
    ShiftAttendanceMode,
    ShiftSlotTemplate,
    CreateShiftAttendanceTemplateLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
    UpdateShiftUserDataLogEntry,
    CreateShiftAttendanceLogEntry,
    ShiftUserData,
    UpdateShiftAttendanceStateLogEntry,
    ShiftAccountEntry,
    ShiftExemption,
    SHIFT_ATTENDANCE_STATES,
)
from tapir.shifts.templatetags.shifts import shift_name_as_class
from tapir.utils.shortcuts import safe_redirect


def time_to_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


# NOTE(Leon Handreke): This is obviously not true for when DST starts and ends, but we don't care, this is just for
# layout and we don't work during the night anyway.
DAY_START_SECONDS = time_to_seconds(time(6, 0))
DAY_END_SECONDS = time_to_seconds(time(22, 0))
DAY_DURATION_SECONDS = DAY_END_SECONDS - DAY_START_SECONDS


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


class ShiftDetailView(LoginRequiredMixin, DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift: Shift = context["shift"]
        slots = shift.slots.all()
        user_is_registered_to_this_shift = (
            ShiftAttendance.objects.with_valid_state()
            .filter(slot__shift=shift, user=self.request.user)
            .exists()
        )

        for slot in slots:
            slot.can_register = slot.user_can_attend(self.request.user)
            slot.can_self_unregister = slot.user_can_self_unregister(self.request.user)
            slot.can_look_for_stand_in = slot.user_can_look_for_standin(
                self.request.user
            )
            slot.show_register_self = not user_is_registered_to_this_shift and (
                slot.get_valid_attendance() is None
                or slot.get_valid_attendance().state
                == ShiftAttendance.State.LOOKING_FOR_STAND_IN
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
        day = datetime.datetime.strptime(kwargs["day"], "%d-%m-%y").date()
        context["shifts"] = Shift.objects.filter(start_time__date=day)
        return context


class SlotRegisterView(PermissionRequiredMixin, SelectedUserViewMixin, CreateView):
    permission_required = "shifts.manage"
    model = ShiftAttendance
    template_name = "shifts/slot_register.html"
    form_class = ShiftAttendanceForm

    def get_initial(self):
        return {"user": self.get_selected_user()}

    def get_slot(self):
        return get_object_or_404(ShiftSlot, pk=self.kwargs["slot_pk"])

    def get_context_data(self, **kwargs):
        kwargs["slot"] = self.get_slot()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.instance.slot = self.get_slot()
        with transaction.atomic():
            response = super().form_valid(form)
            self.get_slot().mark_stand_in_found_if_relevant(self.request.user)
            shift_attendance: ShiftAttendance = self.object
            log_entry = CreateShiftAttendanceLogEntry().populate(
                actor=self.request.user,
                user=self.object.user,
                model=shift_attendance,
            )
            log_entry.slot_name = shift_attendance.slot.name
            log_entry.shift = shift_attendance.slot.shift
            log_entry.save()

        return response

    def get_success_url(self):
        if self.get_selected_user():
            return self.get_selected_user().get_absolute_url()
        return self.object.slot.shift.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"slot_pk": self.kwargs["slot_pk"]})
        return kwargs


class SlotTemplateRegisterView(
    PermissionRequiredMixin, SelectedUserViewMixin, CreateView
):
    permission_required = "shifts.manage"
    model = ShiftAttendanceTemplate
    template_name = "shifts/slot_template_register.html"
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

            shift_attendance_template = self.object
            log_entry = CreateShiftAttendanceTemplateLogEntry().populate(
                actor=self.request.user,
                user=self.object.user,
                model=shift_attendance_template,
            )
            log_entry.slot_template_name = self.object.slot_template.name
            log_entry.shift_template = self.object.slot_template.shift_template
            log_entry.save()

        return response

    def get_success_url(self):
        if self.get_selected_user():
            return self.get_selected_user().get_absolute_url()
        return self.object.slot_template.shift_template.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"slot_template_pk": self.kwargs["slot_template_pk"]})
        return kwargs


class UpdateShiftAttendanceStateBase(PermissionRequiredMixin, UpdateView):
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
            and self.get_attendance().slot.user_can_look_for_standin
        )
        cancel_look_for_standing = (
            state == ShiftAttendance.State.PENDING
            and self.get_attendance().state
            == ShiftAttendance.State.LOOKING_FOR_STAND_IN
        )
        if self_unregister or look_for_standing or cancel_look_for_standing:
            return []
        return ["shifts.manage"]

    def get_success_url(self):
        return self.get_object().slot.shift.get_absolute_url()

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            attendance = self.get_attendance()
            if self.get_state_from_kwargs:
                attendance.state = self.kwargs["state"]
                attendance.save()

            log_entry = UpdateShiftAttendanceStateLogEntry().populate(
                actor=self.request.user,
                user=attendance.user,
                model=attendance,
            )
            log_entry.slot_name = attendance.slot.name
            log_entry.shift = attendance.slot.shift
            log_entry.state = attendance.state
            log_entry.save()

            if attendance.state == ShiftAttendance.State.MISSED:
                self.send_shift_missed_email()

            if attendance.account_entry is not None:
                previous_entry = attendance.account_entry
                attendance.account_entry = None
                attendance.save()
                previous_entry.delete()

            entry_value = None
            if attendance.state == ShiftAttendance.State.MISSED:
                entry_value = -1
            elif attendance.state in [
                ShiftAttendance.State.DONE,
                ShiftAttendance.State.MISSED_EXCUSED,
            ]:
                entry_value = 1

            if entry_value is not None:
                description = f"Shift {SHIFT_ATTENDANCE_STATES[attendance.state]}"
                if "description" in form.data:
                    description = f"{description} ({form.data['description']})"

                entry = ShiftAccountEntry.objects.create(
                    user=attendance.user,
                    value=entry_value,
                    date=attendance.slot.shift.start_time,
                    description=description,
                )
                attendance.account_entry = entry
                attendance.save()

            return response

    def send_shift_missed_email(self):
        attendance = self.get_attendance()

        with translation.override(attendance.user.preferred_language):
            mail = EmailMessage(
                subject=_("You missed your shift!"),
                body=render_to_string(
                    [
                        "shifts/email/shift_missed.html",
                        "shifts/email/shift_missed.default.html",
                    ],
                    {
                        "tapir_user": attendance.user,
                        "shift": attendance.slot.shift,
                        "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
                        "coop_name": settings.COOP_NAME,
                    },
                ),
                from_email=FROM_EMAIL_MEMBER_OFFICE,
                to=[attendance.user.email],
            )
            mail.content_subtype = "html"
            mail.send()


class UpdateShiftAttendanceStateView(UpdateShiftAttendanceStateBase):
    fields = []


class UpdateShiftAttendanceStateWithFormView(UpdateShiftAttendanceStateBase):
    form_class = UpdateShiftAttendanceForm
    get_state_from_kwargs = False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"state": self.kwargs["state"]})
        return kwargs


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def shift_attendance_template_delete(request, pk):
    shift_attendance_template = get_object_or_404(ShiftAttendanceTemplate, pk=pk)
    slot_template = shift_attendance_template.slot_template

    with transaction.atomic():
        log_entry = DeleteShiftAttendanceTemplateLogEntry().populate(
            actor=request.user,
            user=shift_attendance_template.user,
            model=shift_attendance_template,
        )
        log_entry.slot_template_name = slot_template.name
        log_entry.shift_template = slot_template.shift_template
        log_entry.save()

        shift_attendance_template.cancel_attendances(timezone.now())
        shift_attendance_template.delete()

    return safe_redirect(request.GET.get("next"), slot_template.shift_template, request)


@require_POST
@csrf_protect
def shiftslot_register_user(request, pk, user_pk):
    slot = get_object_or_404(ShiftSlot, pk=pk)
    selected_user = get_object_or_404(TapirUser, pk=user_pk)
    if request.user.pk != user_pk and not selected_user.has_perm("shifts.manage"):
        return HttpResponseForbidden(
            "You don't have the rights to register other users to shifts."
        )
    if not slot.user_can_attend(selected_user):
        raise BadRequest(f"User ({selected_user.pk}) can't join shift slot ({slot.pk})")

    with transaction.atomic():
        shift_attendance = ShiftAttendance.objects.create(slot=slot, user=selected_user)
        slot.mark_stand_in_found_if_relevant(request.user)
        log_entry = CreateShiftAttendanceLogEntry().populate(
            actor=request.user,
            user=selected_user,
            model=shift_attendance,
        )
        log_entry.slot_name = shift_attendance.slot.name
        log_entry.shift = shift_attendance.slot.shift
        log_entry.save()

    return safe_redirect(request.GET.get("next"), slot.shift, request)


class ShiftTemplateDetail(LoginRequiredMixin, SelectedUserViewMixin, DetailView):
    template_name = "shifts/shift_template_detail.html"
    model = ShiftTemplate


class ShiftTemplateOverview(LoginRequiredMixin, SelectedUserViewMixin, TemplateView):
    template_name = "shifts/shift_template_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        grouped_per_day = {}
        for weekday in WEEKDAY_CHOICES:
            grouped_per_day[weekday[1]] = OrderedDict()

        groups_ordered_by_name = ShiftTemplateGroup.objects.all().order_by("name")

        for t in (
            ShiftTemplate.objects.all()
            .order_by("start_time")
            .prefetch_related("group")
            .prefetch_related("slot_templates")
            .prefetch_related("slot_templates__attendance_template")
        ):
            template: ShiftTemplate = t
            weekday_group = grouped_per_day[WEEKDAY_CHOICES[template.weekday][1]]
            start_time_as_string = str(template.start_time)
            if start_time_as_string not in weekday_group:
                weekday_group[start_time_as_string] = {}
            time_group = weekday_group[start_time_as_string]
            if template.group.name not in time_group:
                for template_group in groups_ordered_by_name:
                    time_group[template_group.name] = {}
            for template_group in groups_ordered_by_name:
                if template.name not in time_group[template_group.name]:
                    time_group[template_group.name][template.name] = None
            template_group_group = time_group[template.group.name]
            template_group_group[template.name] = template

        context["day_groups"] = grouped_per_day
        context["shift_template_groups"] = [
            group.name for group in ShiftTemplateGroup.objects.all().order_by("name")
        ]
        context["shift_slot_names"] = get_shift_slot_names()
        return context


class CreateShiftView(PermissionRequiredMixin, CreateView):
    permission_required = "shifts.manage"
    model = Shift
    form_class = ShiftCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = "Creating a shift"
        return context


class EditShiftView(PermissionRequiredMixin, UpdateView):
    permission_required = "shifts.manage"
    model = Shift
    form_class = ShiftCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = "Editing a shift"
        return context


class EditShiftUserDataView(PermissionRequiredMixin, UpdateView):
    permission_required = "shifts.manage"
    model = ShiftUserData
    form_class = ShiftUserDataForm

    def get_success_url(self):
        return self.object.user.get_absolute_url()


@register.simple_tag
def get_week_group(target_time: date) -> ShiftTemplateGroup | None:
    for delta in list(range(52)) + list(range(-52, 0)):
        monday = (
            target_time - timedelta(days=target_time.weekday()) + timedelta(weeks=delta)
        )
        monday = datetime.datetime.combine(
            monday, datetime.time(), timezone.now().tzinfo
        )
        sunday = monday + timedelta(days=7)
        shifts = Shift.objects.filter(
            start_time__gte=monday,
            end_time__lte=sunday,
            shift_template__group__isnull=False,
        )
        if not shifts.exists():
            continue

        corrected_week = (
            shifts.first().shift_template.group.get_group_index() - delta
        ) % 4
        return ShiftTemplateGroup.get_group_from_index(corrected_week)

    return None


@register.simple_tag
def get_current_week_group() -> ShiftTemplateGroup:
    return get_week_group(timezone.now())


def get_shift_slot_names():
    shift_slot_names = ShiftSlot.objects.values_list("name", flat=True).distinct()
    shift_slot_names = [
        (shift_name_as_class(name), _(name)) for name in shift_slot_names if name != ""
    ]
    shift_slot_names.append(("", _("General")))
    return shift_slot_names


class ShiftCalendarBaseView(TemplateView):
    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        context_data["nb_days_for_self_unregister"] = Shift.NB_DAYS_FOR_SELF_UNREGISTER
        # Only filter the eight weeks to make things faster
        upcoming_shifts = (
            self.get_queryset()
            .prefetch_related("slots")
            .prefetch_related("slots__attendances")
            .prefetch_related("slots__attendances__user")
            .prefetch_related("slots__slot_template")
            .prefetch_related("slots__slot_template__attendance_template")
            .prefetch_related("slots__slot_template__attendance_template__user")
            .prefetch_related("shift_template")
            .prefetch_related("shift_template__group")
        )

        # A nested dict containing weeks (indexed by the Monday of the week), then days, then a list of shifts
        # OrderedDict[OrderedDict[list]]
        shifts_by_weeks_and_days = OrderedDict()
        week_to_group = {}
        for shift in upcoming_shifts:
            shift_day = shift.start_time.date()
            shift_week_monday = shift_day - timedelta(days=shift_day.weekday())

            # Ensure the nested OrderedDict[OrderedDict[list]] dictionary has the right data structures for the new item
            shifts_by_weeks_and_days.setdefault(shift_week_monday, OrderedDict())
            shifts_by_weeks_and_days[shift_week_monday].setdefault(shift_day, [])

            shifts_by_weeks_and_days[shift_week_monday][shift_day].append(shift)
            if shift.shift_template is not None:
                week_to_group[shift_week_monday] = shift.shift_template.group

        context_data["shifts_by_weeks_and_days"] = shifts_by_weeks_and_days

        context_data["shift_slot_names"] = get_shift_slot_names()
        context_data["week_to_group"] = week_to_group

        return context_data


@register.filter
def dictionary_get(dic, key):
    return dic[key] if key in dic else None


class ShiftCalendarFutureView(LoginRequiredMixin, ShiftCalendarBaseView):
    template_name = "shifts/shift_calendar_future.html"

    def get_queryset(self):
        monday_this_week = datetime.datetime.combine(
            date.today() - timedelta(days=date.today().weekday()),
            datetime.time(),
            timezone.now().tzinfo,
        )
        return Shift.objects.filter(
            start_time__gte=monday_this_week,
            end_time__lt=monday_this_week + datetime.timedelta(days=365),
        ).order_by("start_time")


class ShiftCalendarPastView(PermissionRequiredMixin, ShiftCalendarBaseView):
    permission_required = "shifts.manage"
    template_name = "shifts/shift_calendar_past.html"

    def get_queryset(self):
        return Shift.objects.filter(
            start_time__gte=date.today() - timedelta(days=8 * 7),
            end_time__lt=date.today(),
        ).order_by("start_time")

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        # We order by start time to get proper day and time ordering, but want to display weeks in reverse
        ctx["shifts_by_weeks_and_days"] = OrderedDict(
            reversed(ctx["shifts_by_weeks_and_days"].items())
        )
        return ctx


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
    u = get_object_or_404(TapirUser, pk=user_pk)
    old_shift_user_data = freeze_for_log(u.shift_user_data)

    with transaction.atomic():
        u.shift_user_data.attendance_mode = attendance_mode
        u.shift_user_data.save()
        log_entry = UpdateShiftUserDataLogEntry().populate(
            actor=request.user,
            user=u,
            old_frozen=old_shift_user_data,
            new_model=u.shift_user_data,
        )
        log_entry.save()

    return redirect(u)


class ShiftTemplateGroupCalendar(LoginRequiredMixin, TemplateView):
    template_name = "shifts/shift_template_group_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        date_to_group = {}
        today = timezone.now().date()
        for week in range(52):
            monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week)
            date_to_group[monday] = get_week_group(monday).name
        context["date_to_group"] = date_to_group
        return context


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


def generate_shifts_up_to(target_day: datetime.date):
    target_monday = target_day - datetime.timedelta(days=target_day.weekday())
    current_monday = datetime.date.today() - datetime.timedelta(
        days=datetime.date.today().weekday()
    )

    while current_monday < target_monday:
        current_monday += datetime.timedelta(days=7)
        group = get_week_group(current_monday)
        group.create_shifts(current_monday)


class StatisticsView(LoginRequiredMixin, generic.TemplateView):
    template_name = "shifts/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["members"] = self.get_members_context()
        context["abcd_slots"] = self.get_abcd_slots_context()
        context["weeks"] = self.get_weeks_context()

        return context

    @staticmethod
    def get_members_context():
        context = {}

        active_members = ShareOwner.objects.with_status(MemberStatus.ACTIVE)
        active_users = TapirUser.objects.filter(share_owner__in=active_members)
        context["active_users_count"] = active_users.count()
        exempted_users = ShiftUserData.objects.filter(
            user__in=active_users
        ).is_covered_by_exemption()
        context["exempted_users_count"] = exempted_users.count()
        users_doing_shifts = active_users.exclude(shift_user_data__in=exempted_users)
        context["users_doing_shifts_count"] = users_doing_shifts.count()

        context["abcd_slots_count"] = ShiftSlotTemplate.objects.count()
        context["extra_abcd_slots_count"] = (
            context["abcd_slots_count"] - context["users_doing_shifts_count"]
        )

        members_in_abcd_system = users_doing_shifts.with_shift_attendance_mode(
            ShiftAttendanceMode.REGULAR
        )
        context["members_in_abcd_system_count"] = members_in_abcd_system.count()

        context[
            "members_in_flying_system_count"
        ] = active_users.with_shift_attendance_mode(ShiftAttendanceMode.FLYING).count()

        context["members_in_abcd_system_without_shift_attendance_count"] = (
            members_in_abcd_system.annotate(
                num_template_attendances=Count("shift_attendance_templates")
            )
            .filter(num_template_attendances=0)
            .count()
        )

        return context

    @staticmethod
    def get_abcd_slots_context():
        slot_types = ShiftSlotTemplate.objects.values("name").distinct()
        abcd_slots = {}
        for slot_type in slot_types:
            displayed_name = slot_type["name"]
            if displayed_name == "":
                displayed_name = "General"
            abcd_slots[displayed_name] = {}
            abcd_slots[displayed_name][
                "registered"
            ] = TapirUser.objects.registered_to_shift_slot_name(
                slot_type["name"]
            ).count()
            abcd_slots[displayed_name]["slot_count"] = ShiftSlotTemplate.objects.filter(
                name=slot_type["name"]
            ).count()
        return abcd_slots

    @staticmethod
    def get_weeks_context():
        context = {}
        today = datetime.date.today()
        weeks = {"Last": -1, "Current": 0, "Next": 1}
        for week, delta in weeks.items():
            week_context = {}
            monday = today - timedelta(days=today.weekday()) + timedelta(weeks=delta)
            week_start = datetime.datetime.combine(
                monday, datetime.time(hour=0, minute=0), timezone.now().tzinfo
            )
            week_end = monday + datetime.timedelta(days=7)
            shifts = Shift.objects.filter(
                start_time__gte=week_start,
                end_time__lte=week_end,
            )
            week_context["shifts_count"] = shifts.count()
            week_context["slots_count"] = ShiftSlot.objects.filter(
                shift__in=shifts
            ).count()
            week_context["occupied_count"] = (
                ShiftAttendance.objects.filter(slot__shift__in=shifts)
                .with_valid_state()
                .count()
            )
            week_context["standin_search_count"] = ShiftAttendance.objects.filter(
                slot__shift__in=shifts,
                state=ShiftAttendance.State.LOOKING_FOR_STAND_IN,
            ).count()

            context[week] = week_context

        return context

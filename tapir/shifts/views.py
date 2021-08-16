import datetime
from collections import defaultdict, OrderedDict

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, \
    FormView
from werkzeug.exceptions import BadRequest

from tapir.accounts.models import TapirUser
from tapir.shifts.forms import ShiftCreateForm
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftTemplateGroup,
    ShiftAttendanceTemplate,
    ShiftSlot,
    ShiftAttendanceMode, ShiftSlotTemplate,
)


def time_to_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


# NOTE(Leon Handreke): This is obviously not true for when DST starts and ends, but we don't care, this is just for
# layout and we don't work during the night anyway.
DAY_START_SECONDS = time_to_seconds(datetime.time(6, 0))
DAY_END_SECONDS = time_to_seconds(datetime.time(22, 0))
DAY_DURATION_SECONDS = DAY_END_SECONDS - DAY_START_SECONDS


class UpcomingDaysView(LoginRequiredMixin, TemplateView):
    template_name = "shifts/upcoming_days.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        shifts_by_days = defaultdict(list)

        for shift in Shift.objects.filter(start_time__gte=datetime.date.today()):
            start_time_seconds = time_to_seconds(shift.start_time)
            end_time_seconds = time_to_seconds(shift.end_time)

            position_left = (
                start_time_seconds - DAY_START_SECONDS
            ) / DAY_DURATION_SECONDS
            width = (end_time_seconds - start_time_seconds) / DAY_DURATION_SECONDS
            width -= 0.01  # To make shifts not align completely

            # TODO(Leon Handreke): The name for this var sucks but can't find a better one
            num_required_slots = shift.slots.filter(optional=False).count()
            perc_slots_occupied = shift.get_valid_attendances().count() / float(
                num_required_slots
            )

            shifts_by_days[shift.start_time.date()].append(
                {
                    "title": shift.name,
                    "obj": shift,
                    "position_left": position_left * 100,
                    "width": width * 100,
                    # TODO(Leon Handreke): This style decision, should happen in the template!
                    "block_color": "#ef9a9a"
                    if perc_slots_occupied <= 0.4
                    else ("#a5d6a7" if perc_slots_occupied >= 1 else "#ffe082"),
                    # Have a list of none cause it's easier to loop over in Django templates
                    "free_slots": [None]
                    * (num_required_slots - shift.get_valid_attendances().count()),
                    "attendances": shift.get_attendances().with_valid_state(),
                }
            )

        # Django template language can't loop defaultdict
        today = datetime.date.today()
        context_data["today"] = today
        context_data["shifts_today"] = shifts_by_days[today]
        del shifts_by_days[today]

        context_data["shifts_by_days"] = dict(shifts_by_days)

        return context_data


class ShiftDetailView(LoginRequiredMixin, DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slots = context["shift"].slots.all()
        for slot in slots:
            slot.can_register = slot.user_can_attend(self.request.user)
        context["slots"] = slots
        return context


class SlotTemplateRegisterView(PermissionRequiredMixin, CreateView):
    permission_required = "shifts.manage"
    model = ShiftAttendanceTemplate
    template_name = "shifts/slottemplate_register.html"
    fields = ['user']

    def get_slot_template(self):
        return get_object_or_404(ShiftSlotTemplate, pk=self.kwargs['slot_template_pk'])

    def get_context_data(self, **kwargs):
        kwargs['slot_template'] = self.get_slot_template()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.instance.slot_template = self.get_slot_template()
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.slot_template.shift_template.get_absolute_url()


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def mark_shift_attendance_done(request, pk):
    shift_attendance = get_object_or_404(ShiftAttendance, pk=pk)
    shift_attendance.mark_done()

    return redirect(shift_attendance.slot.shift)


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def mark_shift_attendance_missed(request, pk):
    shift_attendance = get_object_or_404(ShiftAttendance, pk=pk)
    shift_attendance.mark_missed()

    return redirect(shift_attendance.slot.shift)


# TODO(Leon Handreke): Kill this function and make it a page instead that allows to register for different slots
@require_POST
@csrf_protect
@permission_required("shifts.manage")
def shifttemplate_register_user(request, pk, user_pk):
    shift_template = get_object_or_404(ShiftTemplate, pk=pk)
    user = get_object_or_404(TapirUser, pk=user_pk)

    slot_template = shift_template.slot_templates.filter(
        required_capabilities=[], attendance_template__isnull=True
    ).first()
    if not slot_template:
        return BadRequest("No free slots in this shift template")

    ShiftAttendanceTemplate.objects.create(user=user, slot_template=slot_template)
    return redirect(request.GET.get("next", user))


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def slottemplate_unregister_user(request, pk, user_pk):
    user = get_object_or_404(TapirUser, pk=user_pk)
    shift_attendance_template = get_object_or_404(
        ShiftAttendanceTemplate, user__pk=user_pk, slot_template__pk=pk
    )
    shift_attendance_template.delete()
    return redirect(request.GET.get("next", user))


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
        raise BadRequest(
            "User ({0}) can't join shift slot ({1})".format(selected_user.pk, slot.pk)
        )

    ShiftAttendance.objects.create(slot=slot, user=selected_user)
    return redirect(request.GET.get("next", slot.shift))


class ShiftTemplateDetail(PermissionRequiredMixin, DetailView):
    permission_required = "shifts.manage"
    template_name = "shifts/shift_template_detail.html"
    model = ShiftTemplate


class ShiftTemplateOverview(LoginRequiredMixin, TemplateView):
    template_name = "shifts/shift_template_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        grouped_per_day = {}
        for weekday in WEEKDAY_CHOICES:
            grouped_per_day[weekday[1]] = OrderedDict()

        for t in ShiftTemplate.objects.all().order_by("start_time"):
            template: ShiftTemplate = t
            weekday_group = grouped_per_day[WEEKDAY_CHOICES[template.weekday][1]]
            start_time_as_string = str(template.start_time)
            if start_time_as_string not in weekday_group:
                weekday_group[start_time_as_string] = {}
            time_group = weekday_group[start_time_as_string]
            if template.group.name not in time_group:
                for template_group in ShiftTemplateGroup.objects.all().order_by("name"):
                    time_group[template_group.name] = {}
            for template_group in ShiftTemplateGroup.objects.all().order_by("name"):
                if template.name not in time_group[template_group.name]:
                    time_group[template_group.name][template.name] = None
            template_group_group = time_group[template.group.name]
            template_group_group[template.name] = template

        context["day_groups"] = grouped_per_day
        context["shift_template_groups"] = [
            group.name for group in ShiftTemplateGroup.objects.all().order_by("name")
        ]
        return context


class ShiftTemplateOverviewRegister(ShiftTemplateOverview):
    """Overview to register a given user to a ShiftTemplate"""

    permission_required = "shifts.manage"
    template_name = "shifts/shift_template_overview_register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = get_object_or_404(TapirUser, pk=self.kwargs["user_pk"])
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


class UpcomingShiftsAsTimetable(LoginRequiredMixin, TemplateView):
    template_name = "shifts/timetable.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        upcoming_shifts = Shift.objects.filter(
            start_time__gte=datetime.date.today()
        ).order_by("start_time")[:100]
        shifts_by_days = dict()
        day_start_time = None
        for test in upcoming_shifts:
            shift: Shift = test
            shift_day = shift.start_time.date()
            if shift_day not in shifts_by_days:
                shifts_by_days[shift_day] = dict()
                day_start_time = shift.start_time

            shifts_by_name = shifts_by_days[shift_day]
            if shift.name not in shifts_by_name:
                shifts_by_name[shift.name] = []

            shift_display_infos = dict()
            shift_display_infos["shift"] = shift
            duration = (shift.end_time - shift.start_time).total_seconds() / 3600
            shift_display_infos["height"] = duration * 50
            previous_time = day_start_time
            if len(shifts_by_name[shift.name]) > 0:
                previous_time = shifts_by_name[shift.name][-1]["shift"].end_time
            shift_display_infos["margin_top"] = (
                (shift.start_time - previous_time).total_seconds() / 3600
            ) * 50
            shifts_by_name[shift.name].append(shift_display_infos)

        context_data["shifts_by_days"] = shifts_by_days
        return context_data


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def set_user_attendance_mode_flying(self, user_pk):
    u = get_object_or_404(TapirUser, pk=user_pk)
    u.shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
    u.shift_user_data.save()

    return redirect(u)


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def set_user_attendance_mode_regular(self, user_pk):
    u = get_object_or_404(TapirUser, pk=user_pk)
    u.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
    u.shift_user_data.save()

    return redirect(u)

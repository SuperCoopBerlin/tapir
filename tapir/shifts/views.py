import datetime
from collections import defaultdict

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.forms import ShiftCreateForm
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftTemplateGroup,
    ShiftAttendanceTemplate,
)


def time_to_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


# NOTE(Leon Handreke): This is obviously not true for when DST starts and ends, but we don't care, this is just for
# layout and we don't work during the night anyway.
DAY_START_SECONDS = time_to_seconds(datetime.time(6, 0))
DAY_END_SECONDS = time_to_seconds(datetime.time(22, 0))
DAY_DURATION_SECONDS = DAY_END_SECONDS - DAY_START_SECONDS


class UpcomingDaysView(PermissionRequiredMixin, TemplateView):
    permission_required = "shifts.manage"
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
            perc_slots_occupied = shift.get_valid_attendances().count() / float(
                shift.num_slots
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
                    * (shift.num_slots - shift.get_valid_attendances().count()),
                    "attendances": shift.get_valid_attendances().all(),
                }
            )

        # Django template language can't loop defaultdict
        today = datetime.date.today()
        context_data["today"] = today
        context_data["shifts_today"] = shifts_by_days[today]
        del shifts_by_days[today]

        context_data["shifts_by_days"] = dict(shifts_by_days)

        return context_data


class ShiftDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "shifts.manage"
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        shift: Shift = context["shift"]
        attendances = list(shift.attendances.all())
        while len(attendances) < shift.num_slots:
            attendances.append(None)
        context["attendances"] = attendances

        context["can_join"] = user_can_join_shift(self.request.user, shift)

        return context


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def mark_shift_attendance_done(request, pk):
    shift_attendance = ShiftAttendance.objects.get(pk=pk)
    shift_attendance.mark_done()

    return redirect(shift_attendance.shift)


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def mark_shift_attendance_missed(request, pk):
    shift_attendance = ShiftAttendance.objects.get(pk=pk)
    shift_attendance.mark_missed()

    return redirect(shift_attendance.shift)


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def shifttemplate_register_user(request, pk, user_pk):
    shift_template = get_object_or_404(ShiftTemplate, pk=pk)
    user = get_object_or_404(TapirUser, pk=user_pk)

    ShiftAttendanceTemplate.objects.create(user=user, shift_template=shift_template)
    return redirect(request.GET.get("next", user))


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def shifttemplate_unregister_user(request, pk, user_pk):
    user = get_object_or_404(TapirUser, pk=user_pk)
    shift_attendance_template = get_object_or_404(
        ShiftAttendanceTemplate, user__pk=user_pk, shift_template__pk=pk
    )
    shift_attendance_template.delete()
    return redirect(request.GET.get("next", user))


class ShiftTemplateOverview(PermissionRequiredMixin, TemplateView):
    permission_required = "shifts.manage"
    template_name = "shifts/shift_template_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        grouped_per_day = {}
        for weekday in WEEKDAY_CHOICES:
            grouped_per_day[weekday[1]] = {}

        for t in ShiftTemplate.objects.all().order_by("name"):
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


@permission_required("shifts.manage")
def register_user_to_shift(request, pk):
    shift = Shift.objects.get(pk=pk)
    user: TapirUser = request.user
    if not user_can_join_shift(user, shift):
        raise Exception("User ({0}) can't join shift ({1})".format(user.id, shift.id))
    ShiftAttendance.objects.create(shift=shift, user=user)

    return redirect(shift)


def user_can_join_shift(user: TapirUser, shift: Shift) -> bool:
    can_join = len(shift.attendances.filter(user=user)) == 0
    share_owner = ShareOwner.objects.filter(user=user)
    if len(share_owner) > 0:
        can_join = can_join and not ShareOwner.objects.get(user=user).is_investing
    return can_join


class UpcomingShiftsAsTimetable(PermissionRequiredMixin, TemplateView):
    permission_required = "shifts.manage"
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

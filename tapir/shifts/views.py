import datetime
from collections import defaultdict

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.handlers.wsgi import WSGIRequest
from django.forms import Form, modelform_factory
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import make_aware
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, UpdateView

from tapir.accounts.models import TapirUser
from tapir.shifts.models import Shift, ShiftAttendance, ShiftTemplate, WEEKDAY_CHOICES, ShiftTemplateGroup, ShiftAttendanceTemplate


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

            position_left = (start_time_seconds - DAY_START_SECONDS) / DAY_DURATION_SECONDS
            width = (end_time_seconds - start_time_seconds) / DAY_DURATION_SECONDS
            width -= 0.01  # To make shifts not align completely

            # TODO(Leon Handreke): The name for this var sucks but can't find a better one
            perc_slots_occupied = shift.get_valid_attendances().count() / float(shift.num_slots)
            shifts_by_days[shift.start_time.date()].append(
                {
                    "title": shift.name,
                    "obj": shift,
                    "position_left": position_left * 100,
                    "width": width * 100,
                    # TODO(Leon Handreke): This style decision, should happen in the template!
                    "block_color": "#ef9a9a" if perc_slots_occupied <= 0.4 else ("#a5d6a7" if perc_slots_occupied >= 1 else "#ffe082"),
                    # Have a list of none cause it's easier to loop over in Django templates
                    "free_slots": [None] * (shift.num_slots - shift.get_valid_attendances().count()),
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


class ShiftDetailView(DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"


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


def populate_shifts(request):
    for delta in range(-7, 7):
        date = datetime.date.today() - datetime.timedelta(days=delta)
        morning = datetime.datetime.combine(date, datetime.time(hour=8))
        noon = datetime.datetime.combine(date, datetime.time(hour=12))
        evening = datetime.datetime.combine(date, datetime.time(hour=16))

        Shift.objects.get_or_create(
            name="Cashier morning",
            start_time=morning,
            end_time=noon,
            num_slots=4,
        )

        Shift.objects.get_or_create(
            name="Cashier afternoon",
            start_time=noon,
            end_time=evening,
            num_slots=4,
        )

        Shift.objects.get_or_create(
            name="Storage morning",
            start_time=morning,
            end_time=noon,
            num_slots=3,
        )

        Shift.objects.get_or_create(
            name="Storage afternoon",
            start_time=noon,
            end_time=evening,
            num_slots=3,
        )

    return HttpResponse("Populated shift templates for today")


def populate_user_shifts(request, user_id):
    user = TapirUser.objects.get(pk=user_id)

    date = datetime.date.today() - datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(date, datetime.time(hour=8))
    shift = Shift.objects.get(name="Cashier morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(shift=shift, user=user, state=ShiftAttendance.State.DONE)

    date = datetime.date.today() - datetime.timedelta(days=2)
    start_time = datetime.datetime.combine(date, datetime.time(hour=8))
    shift = Shift.objects.get(name="Storage morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift,
        user=user,
        state=ShiftAttendance.State.MISSED_EXCUSED,
        excused_reason="Was sick",
    )

    date = datetime.date.today() + datetime.timedelta(days=1)
    start_time = datetime.datetime.combine(date, datetime.time(hour=8))
    shift = Shift.objects.get(name="Cashier morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(shift=shift, user=user, state=ShiftAttendance.State.CANCELLED)

    start_time = datetime.datetime.combine(date, datetime.time(hour=12))
    shift = Shift.objects.get(name="Cashier afternoon", start_time=start_time)
    ShiftAttendance.objects.get_or_create(shift=shift, user=user, state=ShiftAttendance.State.PENDING)

    date = datetime.date.today() + datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(date, datetime.time(hour=12))
    shift = Shift.objects.get(name="Storage afternoon", start_time=start_time)
    ShiftAttendance.objects.get_or_create(shift=shift, user=user, state=ShiftAttendance.State.PENDING)

    return HttpResponse("Populated user " + str(user_id) + " shifts")


def populate_template_groups(request: WSGIRequest):
    for week in ["A", "B", "C", "D"]:
        ShiftTemplateGroup.objects.get_or_create(name="Week " + week)
    return HttpResponse("Populated template groups")


def populate_shift_templates(request: WSGIRequest):
    populate_template_groups(request)
    names = ["Organize the shop", "Cashier"]
    start_hours = [9, 12, 15]
    for weekday in WEEKDAY_CHOICES[:-1]:
        for template_group in ShiftTemplateGroup.objects.all():
            for name in names:
                for start_hour in start_hours:
                    start_time = datetime.time(hour=start_hour)
                    end_time = datetime.time(hour=start_hour + 3)
                    ShiftTemplate.objects.get_or_create(name=name, group=template_group, weekday=weekday[0], start_time=start_time, end_time=end_time, num_slots=4)

    for weekday in [WEEKDAY_CHOICES[2], WEEKDAY_CHOICES[5]]:
        for template_group in ShiftTemplateGroup.objects.all():
            start_time = datetime.time(hour=18)
            end_time = datetime.time(hour=18 + 3)
            name = "Store cleaning"
            ShiftTemplate.objects.get_or_create(name=name, group=template_group, weekday=weekday[0], start_time=start_time, end_time=end_time, num_slots=3)

    for group_name in ["A", "C"]:
        start_time = datetime.time(hour=9)
        end_time = datetime.time(hour=9 + 3)
        name = "Inventory"
        template_group = ShiftTemplateGroup.objects.get(name="Week " + group_name)
        ShiftTemplate.objects.get_or_create(name=name, group=template_group, weekday=weekday[0], start_time=start_time, end_time=end_time, num_slots=3)

    for group_name in ["B", "D"]:
        start_time = datetime.time(hour=14)
        end_time = datetime.time(hour=14 + 3)
        name = "Storage cleaning"
        template_group = ShiftTemplateGroup.objects.get(name="Week " + group_name)
        ShiftTemplate.objects.get_or_create(name=name, group=template_group, weekday=weekday[0], start_time=start_time, end_time=end_time, num_slots=3)

    return HttpResponse("Populated shift templates")

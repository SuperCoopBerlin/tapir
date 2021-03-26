import datetime
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.forms import Form, modelform_factory
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, UpdateView

from tapir.shifts.models import Shift, ShiftAttendance


def time_to_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


# NOTE(Leon Handreke): This is obviously not true for when DST starts and ends, but we don't care, this is just for
# layout and we don't work during the night anyway.
DAY_START_SECONDS = time_to_seconds(datetime.time(6, 0))
DAY_END_SECONDS = time_to_seconds(datetime.time(22, 0))
DAY_DURATION_SECONDS = DAY_END_SECONDS - DAY_START_SECONDS


class UpcomingDaysView(TemplateView):
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


class ShiftDetailView(DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"


@require_POST
@csrf_protect
@login_required
def mark_shift_attendance_done(request, pk):
    shift_attendance = ShiftAttendance.objects.get(pk=pk)
    shift_attendance.mark_done()

    return redirect(shift_attendance.shift)


@require_POST
@csrf_protect
@login_required
def mark_shift_attendance_missed(request, pk):
    shift_attendance = ShiftAttendance.objects.get(pk=pk)
    shift_attendance.mark_missed()

    return redirect(shift_attendance.shift)

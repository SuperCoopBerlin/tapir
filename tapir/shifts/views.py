import datetime
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.forms import Form, modelform_factory
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, UpdateView

from tapir.shifts.models import Shift, ShiftAttendance


class UpcomingDaysView(TemplateView):

    template_name = "shifts/upcoming_days.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        shifts_by_days = defaultdict(list)
        for shift in Shift.objects.filter(start_time__gte=datetime.date.today()):
            shifts_by_days[shift.start_time.date()].append(shift)

        # Django template language can't loop defaultdict
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

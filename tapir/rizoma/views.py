from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
import datetime
from django.utils import timezone
from collections import OrderedDict
from tapir.shifts.models import Shift
from tapir.shifts.models import ShiftSlot
from tapir.shifts.templatetags.shifts import shift_name_as_class
from django.utils.translation import gettext_lazy as _
from tapir.rizoma.utils import format_shift_for_template

from datetime import date, timedelta
from django.urls import reverse


# based on the ShiftCalendarView in shifts/views/calendars.py
class RizomaAllShiftsView(LoginRequiredMixin, TemplateView):
    template_name = "rizoma/all_shifts.html"
    DATE_FORMAT = "%Y-%m-%d"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)

        try:
            date_from = (
                datetime.datetime.strptime(
                    self.request.GET["date_from"], self.DATE_FORMAT
                ).date()
                if "date_from" in self.request.GET.keys()
                else timezone.now().date()
            )
            date_to = (
                datetime.datetime.strptime(
                    self.request.GET["date_to"], self.DATE_FORMAT
                ).date()
                if "date_to" in self.request.GET.keys()
                else date_from + datetime.timedelta(days=7)
            )
        except:
            date_from = timezone.now().date()
            date_to = date_from + datetime.timedelta(days=7)

        context_data["date_from"] = date_from.strftime(self.DATE_FORMAT)
        context_data["date_to"] = date_to.strftime(self.DATE_FORMAT)

        context_data["nb_days_for_self_unregister"] = Shift.NB_DAYS_FOR_SELF_UNREGISTER
        # Because the shift views show a lot of shifts,
        # we preload all related objects to avoid doing many database requests.
        shifts = (
            Shift.objects.prefetch_related("slots")
            .prefetch_related("slots__attendances")
            .prefetch_related("slots__attendances__user")
            .prefetch_related("slots__slot_template")
            .prefetch_related("slots__slot_template__attendance_template")
            .prefetch_related("slots__slot_template__attendance_template__user")
            .prefetch_related("shift_template")
            .prefetch_related("shift_template__group")
            .filter(
                start_time__gte=date_from,
                start_time__lt=date_to + datetime.timedelta(days=1),
                deleted=False,
            )
            .order_by("start_time")
        )

        # A nested dict containing weeks (indexed by the Monday of the week), then days, then a list of shifts
        # OrderedDict[OrderedDict[list]]
        shifts_by_weeks_and_days = OrderedDict()
        week_to_group = {}
        for shift in shifts:
            shift_day = shift.start_time.date()
            shift_week_monday = shift_day - datetime.timedelta(days=shift_day.weekday())

            # Ensure the nested OrderedDict[OrderedDict[list]] dictionary has the right data structures for the new item
            shifts_by_weeks_and_days.setdefault(shift_week_monday, OrderedDict())
            shifts_by_weeks_and_days[shift_week_monday].setdefault(shift_day, [])

            shifts_by_weeks_and_days[shift_week_monday][shift_day].append(shift)

            if shift.shift_template is not None:
                week_to_group[shift_week_monday] = shift.shift_template.group

        # A dict containing the shifts times and the shifts names for each day
        shifts_infos_by_day = OrderedDict()
        for shift in shifts:
            shift_day = shift.start_time.date()

            if shifts_infos_by_day.get(shift_day) is None:
                shifts_infos_by_day[shift_day] = {
                    "times": [],
                    "names": [],
                    "shifts": [],
                }

            infos = shifts_infos_by_day[shift_day]
            shift_times = {
                "start_time": shift.start_time,
                "end_time": shift.end_time,
            }

            has_this_shift_time = any(t['start_time'] == shift_times['start_time'] and t['end_time'] == shift_times['end_time'] for t in infos["times"])
            if not has_this_shift_time:
                shifts_infos_by_day[shift_day]["times"].append(shift_times)

            if shift.slots.first().name not in infos["names"]:
                shifts_infos_by_day[shift_day]["names"].append(shift.slots.first().name)

            shifts_infos_by_day[shift_day]["shifts"].append(format_shift_for_template(shift, False))

        context_data["shifts_by_weeks_and_days"] = shifts_by_weeks_and_days

        context_data["shift_slot_names"] = get_shift_slot_names()
        context_data["week_to_group"] = week_to_group

        context_data["shifts_infos_by_day"] = shifts_infos_by_day

        context_data["week_ranges"] = get_week_ranges({
            "start": date_from,
            "end": date_to,
        })
        # Find the selected week range in week_ranges
        current_week_range = next(
            (
                week
                for week in context_data["week_ranges"]
                if week["start"] == date_from and week["end"] == date_to
            ),
            None
        )
        context_data["current_week_range"] = current_week_range if current_week_range is not None else {
            "start": date_from,
            "end": date_to,
        }
        context_data["next_week_range"] = {
            "start": context_data["current_week_range"].get("start") + timedelta(days=7),
            "end": context_data["current_week_range"].get("end") + timedelta(days=7),
        }
        context_data["previous_week_range"] = {
            "start": context_data["current_week_range"].get("start") - timedelta(days=7),
            "end": context_data["current_week_range"].get("end") - timedelta(days=7),
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


def get_week_ranges(current_week_range):
        if current_week_range.get("start") and current_week_range.get("end"):
            current_start = current_week_range.get("start")
            current_end = current_week_range.get("end")
        else:
            current_start = timezone.now().date()
            current_end = timezone.now().date() + timedelta(days=6)

        today = date.today()
        # Find the most recent Monday (or today if today is Monday)
        start_of_week = today - timedelta(days=today.weekday())
        week_ranges = []
        for i in range(10):
            week_start = start_of_week + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            week_ranges.append({
                "start": week_start,
                "end": week_end,
                "url": reverse("shifts:calendar") + f"?date_from={week_start}&date_to={week_end}",
                "is_selected": week_start <= current_start and week_end >= current_end,
            })
        # Pass week_ranges to the template context
        return week_ranges

import datetime
from calendar import MONDAY
from collections import OrderedDict
from datetime import timedelta, date, time

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from weasyprint import HTML

from tapir.shifts.models import (
    Shift,
    WEEKDAY_CHOICES,
    ShiftTemplateGroup,
    ShiftTemplate,
)
from tapir.shifts.templatetags.shifts import get_week_group
from tapir.shifts.views.views import get_shift_slot_names, SelectedUserViewMixin
from tapir.shifts.utils import ColorHTMLCalendar


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


class ShiftCalendarFutureView(LoginRequiredMixin, ShiftCalendarBaseView):
    template_name = "shifts/shift_calendar_future.html"

    def get_queryset(self):
        monday_this_week = datetime.combine(
            date.today() - timedelta(days=date.today().weekday()),
            time(),
            timezone.now().tzinfo,
        )
        return Shift.objects.filter(
            start_time__gte=monday_this_week,
            end_time__lt=monday_this_week + timedelta(days=365),
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
        context = super().get_context_data(*args, **kwargs)
        # We order by start time to get proper day and time ordering, but want to display weeks in reverse
        context["shifts_by_weeks_and_days"] = OrderedDict(
            reversed(context["shifts_by_weeks_and_days"].items())
        )
        return context


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


class ShiftTemplateGroupCalendar(LoginRequiredMixin, TemplateView):
    template_name = "shifts/shift_template_group_calendar.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # TODO Frederik: a static calendar.html would accelerate
        thisyear = date.today().year
        start_date = date(thisyear, 1, 1)
        end_date = date(thisyear, 12, 31)
        delta = end_date - start_date  # returns timedelta
        shift_dict = {}
        for i in range(delta.days + 1):
            # iterate through days of year
            day = start_date + datetime.timedelta(days=i)
            monday = day - datetime.timedelta(days=day.weekday() % 7)
            if monday not in shift_dict.keys():
                # populate with shift names at first day of week
                shift_dict[monday] = get_week_group(monday).name
        cal = ColorHTMLCalendar(firstweekday=MONDAY, shift_dict=shift_dict)
        html_result = cal.formatyear(theyear=thisyear, width=4)
        # TODO relative paths: HOWTO?
        HTML(string=html_result).write_pdf(
            "tapir/shifts/static/shifts/ABCD_weeks_calendar.pdf",
            stylesheets=["tapir/shifts/static/shifts/css/calendar.css"],
        )
        context["shiftcal"] = mark_safe(html_result)
        return context

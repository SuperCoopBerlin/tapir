import datetime
from calendar import MONDAY
from collections import OrderedDict

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
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
from tapir.shifts.utils import ColorHTMLCalendar
from tapir.shifts.views.views import get_shift_slot_names, SelectedUserViewMixin
from tapir.utils.shortcuts import get_monday


class ShiftCalendarBaseView(TemplateView):
    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)

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
            shift_week_monday = shift_day - datetime.timedelta(days=shift_day.weekday())

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
        monday_this_week = datetime.datetime.combine(
            datetime.date.today()
            - datetime.timedelta(days=datetime.date.today().weekday()),
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
            start_time__gte=datetime.date.today() - datetime.timedelta(days=8 * 7),
            end_time__lt=datetime.date.today(),
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        displayed_year = self.kwargs.get("year", datetime.date.today().year)

        monday_to_week_group_map = {}
        current_monday = get_monday(datetime.date(year=displayed_year, month=1, day=1))
        while current_monday.year <= displayed_year:
            monday_to_week_group_map[current_monday] = get_week_group(
                current_monday
            ).name
            current_monday += datetime.timedelta(days=7)

        colored_calendar = ColorHTMLCalendar(
            firstweekday=MONDAY, monday_to_week_group_map=monday_to_week_group_map
        )
        rendered_calendar = colored_calendar.formatyear(theyear=displayed_year, width=4)

        context["rendered_calendar"] = mark_safe(rendered_calendar)
        context["displayed_year"] = displayed_year

        return context


class ShiftTemplateGroupCalendarAsPdf(ShiftTemplateGroupCalendar):
    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(*args, **kwargs)

    def get(self, *args, **kwargs):
        context = self.get_context_data()
        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f"filename=shiftcalendar_{context['displayed_year']}.pdf"
        html = context["rendered_calendar"]
        HTML(string=html).write_pdf(
            response, stylesheets=["tapir/shifts/static/shifts/css/calendar.css"]
        )
        return response

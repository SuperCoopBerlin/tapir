import datetime
from calendar import MONDAY
from collections import OrderedDict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from weasyprint import HTML

from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.shifts.models import (
    Shift,
    WEEKDAY_CHOICES,
    ShiftTemplateGroup,
    ShiftTemplate,
)
from tapir.shifts.templatetags.shifts import get_week_group
from tapir.shifts.utils import ColorHTMLCalendar
from tapir.shifts.views.views import get_shift_slot_names, SelectedUserViewMixin
from tapir.utils.shortcuts import get_monday, set_header_for_file_download


class ShiftCalendarView(LoginRequiredMixin, TemplateView):
    template_name = "shifts/shift_calendar_future.html"
    DATE_FORMAT = "%Y-%m-%d"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)

        date_from = (
            datetime.datetime.strptime(
                self.request.GET["date_from"], self.DATE_FORMAT
            ).date()
            if "date_from" in self.request.GET.keys()
            else get_monday(timezone.now().date())
        )
        date_to = (
            datetime.datetime.strptime(
                self.request.GET["date_to"], self.DATE_FORMAT
            ).date()
            if "date_to" in self.request.GET.keys()
            else date_from + datetime.timedelta(days=60)
        )
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

        context_data["shifts_by_weeks_and_days"] = shifts_by_weeks_and_days

        context_data["shift_slot_names"] = get_shift_slot_names()
        context_data["week_to_group"] = week_to_group

        return context_data


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

        displayed_year = self.kwargs.get("year", timezone.now().today().year)

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
        response = HttpResponse(content_type=CONTENT_TYPE_PDF)
        set_header_for_file_download(
            response, f"shiftcalendar_{context['displayed_year']}"
        )
        html = context["rendered_calendar"]
        HTML(string=html).write_pdf(
            response, stylesheets=["tapir/shifts/static/shifts/css/calendar.css"]
        )
        return response

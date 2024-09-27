import datetime

from chartjs.views import JSONView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.views import generic

from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.models import (
    ShiftAttendance,
    Shift,
)
from tapir.statistics.utils import (
    build_line_chart_data,
)
from tapir.utils.shortcuts import get_first_of_next_month


# The main statistic view is intended for members and is accessible for all.
# The views from this file are intended for deciders. They are not accessible for all to avoid confusion,
# as they may be less well presented or harder to interpret


class StateDistributionView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    template_name = "statistics/state_distribution.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data


class StateDistributionJsonView(LoginRequiredMixin, PermissionRequiredMixin, JSONView):
    permission_required = PERMISSION_SHIFTS_MANAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates_from_first_shift_to_today = None

    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=[
                date for date in self.get_and_cache_dates_from_first_shift_to_today()
            ],
            y_axis_values=self.get_data(),
            data_labels=[
                "Pending",
                "Attended",
                "Cancelled",
                "No show",
                "Excused",
                "Looking for standing",
            ],
        )

    def get_and_cache_dates_from_first_shift_to_today(self):
        if self.dates_from_first_shift_to_today is None:
            self.dates_from_first_shift_to_today = (
                self.get_dates_from_first_shift_to_today()
            )
        return self.dates_from_first_shift_to_today

    @staticmethod
    def get_dates_from_first_shift_to_today():
        first_shift = Shift.objects.order_by("start_time").first()
        if not first_shift:
            return []

        current_date = first_shift.start_time.date().replace(day=1)
        end_date = timezone.now().date() + datetime.timedelta(days=1)
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        return dates

    def get_data(self):
        return [
            self.get_ratio_for_state(state[0])
            for state in ShiftAttendance.State.choices
        ]

    def get_ratio_for_state(self, state):
        return [
            self.get_ratio_for_state_and_date(state, at_date)
            for at_date in self.get_and_cache_dates_from_first_shift_to_today()
        ]

    @classmethod
    def get_ratio_for_state_and_date(cls, state, at_date):
        end_date = get_first_of_next_month(at_date) - datetime.timedelta(days=1)
        attendances = ShiftAttendance.objects.filter(
            slot__shift__start_time__gte=at_date,
            slot__shift__start_time__lte=end_date,
            slot__shift__cancelled=False,
        )

        nb_total_attendances = attendances.count()
        nb_attendances_of_state = attendances.filter(state=state).count()

        return nb_attendances_of_state

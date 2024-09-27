import datetime

from chartjs.views import JSONView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import OuterRef, Subquery, CharField
from django.utils import timezone
from django.views import generic

from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftAttendanceMode,
    ShiftUserData,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.statistics.utils import (
    build_line_chart_data,
    FORMAT_TICKS_PERCENTAGE,
)
from tapir.utils.shortcuts import get_first_of_next_month


# The main statistic view is intended for members and is accessible for all.
# The views from this file are intended for deciders. They are not accessible for all to avoid confusion,
# as they may be less well presented or harder to interpret


class ShiftCancellingRateView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    template_name = "statistics/shift_cancelling_rate.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data


class ShiftCancellingRateJsonView(
    LoginRequiredMixin, PermissionRequiredMixin, JSONView
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    SELECTIONS = [
        "abcd_members",
        "flying_members",
        "frozen_members",
        "abcd_shifts",
        "flying_shifts",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates_from_first_shift_to_today = None

    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=[
                date for date in self.get_and_cache_dates_from_first_shift_to_today()
            ],
            y_axis_values=self.get_data(),
            data_labels=self.SELECTIONS,
            y_axis_min=0,
            y_axis_max=1,
            format_ticks=FORMAT_TICKS_PERCENTAGE,
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
        current_date = datetime.date(year=2024, month=3, day=1)
        end_date = timezone.now().date() + datetime.timedelta(days=1)
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        if len(dates) > 0 and dates[-1] != end_date:
            dates.append(end_date)

        return dates

    def get_data(self):
        return [
            self.get_cancel_rate_for_selection(selection)
            for selection in self.SELECTIONS
        ]

    def get_cancel_rate_for_selection(self, selection: str):
        return [
            self.get_cancel_rate_for_selection_at_date(selection, at_date)
            for at_date in self.get_and_cache_dates_from_first_shift_to_today()
        ]

    @staticmethod
    def filter_attendance_by_attendance_mode_of_member_at_date(
        attendances, attendance_mode, at_date
    ):
        shift_user_datas = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_date(
            ShiftUserData.objects.all(), at_date
        )
        attendances = attendances.annotate(
            attendance_mode=Subquery(
                shift_user_datas.filter(user_id=OuterRef("user_id")).values(
                    ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE
                ),
                output_field=CharField(),
            )
        )

        return attendances.filter(attendance_mode=attendance_mode)

    def get_cancel_rate_for_selection_at_date(self, selection, at_date):
        end_date = get_first_of_next_month(at_date) - datetime.timedelta(days=1)
        attendances = ShiftAttendance.objects.exclude(
            state=ShiftAttendance.State.PENDING
        ).filter(
            slot__shift__start_time__gte=at_date, slot__shift__start_time__lte=end_date
        )

        # Only pick one attendance per slot, choosing the most recently updated one
        attendances = attendances.order_by("slot", "-last_state_update").distinct(
            "slot"
        )

        if selection == "abcd_members":
            attendances = self.filter_attendance_by_attendance_mode_of_member_at_date(
                attendances, ShiftAttendanceMode.REGULAR, at_date
            )
        elif selection == "flying_members":
            attendances = self.filter_attendance_by_attendance_mode_of_member_at_date(
                attendances, ShiftAttendanceMode.FLYING, at_date
            )
        elif selection == "frozen_members":
            attendances = self.filter_attendance_by_attendance_mode_of_member_at_date(
                attendances, ShiftAttendanceMode.FROZEN, at_date
            )
        elif selection == "abcd_shifts":
            return 0
        elif selection == "flying_shifts":
            return 0

        nb_total_attendances = attendances.count()
        nb_attended = attendances.filter(state=ShiftAttendance.State.DONE).count()
        nb_not_attended = nb_total_attendances - nb_attended

        return nb_not_attended / (nb_total_attendances or 1)

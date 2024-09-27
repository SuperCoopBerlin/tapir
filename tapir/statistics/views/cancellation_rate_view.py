import datetime

from chartjs.views import JSONView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import OuterRef, Subquery, CharField
from django.utils import timezone
from django.views import generic

from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceMode,
    ShiftUserData,
)
from tapir.shifts.services.is_shift_attendance_from_template_service import (
    IsShiftAttendanceFromTemplateService,
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


class ShiftCountByCategoryJsonView(
    LoginRequiredMixin, PermissionRequiredMixin, JSONView
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    SELECTION_ABCD_MEMBERS = "ABCD members"
    SELECTION_FLYING_MEMBERS = "Flying members"
    SELECTION_FROZEN_MEMBERS = "Frozen members"
    SELECTION_ABCD_SHIFTS = "ABCD shifts"
    SELECTION_FLYING_SHIFTS = "Flying shifts"
    SELECTIONS = [
        SELECTION_ABCD_MEMBERS,
        SELECTION_FLYING_MEMBERS,
        SELECTION_FROZEN_MEMBERS,
        SELECTION_ABCD_SHIFTS,
        SELECTION_FLYING_SHIFTS,
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
        )

    def get_and_cache_dates_from_first_shift_to_today(self):
        if self.dates_from_first_shift_to_today is None:
            self.dates_from_first_shift_to_today = (
                self.get_dates_from_first_shift_to_today()
            )
        return self.dates_from_first_shift_to_today

    @staticmethod
    def get_dates_from_first_shift_to_today():
        current_date = datetime.date(year=2024, month=1, day=1)
        end_date = timezone.now().date() + datetime.timedelta(days=1)
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        return dates

    def get_data(self):
        return [
            self.get_cancel_count_for_selection(selection)
            for selection in self.SELECTIONS
        ]

    def get_cancel_count_for_selection(self, selection: str):
        return [
            self.get_number_of_attendances_for_selection_at_date(selection, at_date)
            for at_date in self.get_and_cache_dates_from_first_shift_to_today()
        ]

    def get_number_of_attendances_for_selection_at_date(self, selection: str, at_date):
        return self.get_attendances_for_selection_at_date(selection, at_date).count()

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

    @classmethod
    def get_attendances_for_selection_at_date(cls, selection, at_date):
        end_date = get_first_of_next_month(at_date) - datetime.timedelta(days=1)
        attendances = ShiftAttendance.objects.exclude(
            state=ShiftAttendance.State.PENDING
        ).filter(
            slot__shift__start_time__gte=at_date,
            slot__shift__start_time__lte=end_date,
            slot__shift__cancelled=False,
        )

        # Only pick one attendance per slot, choosing the most recently updated one
        attendances = attendances.order_by("slot", "-last_state_update").distinct(
            "slot"
        )

        if selection == cls.SELECTION_ABCD_MEMBERS:
            attendances = cls.filter_attendance_by_attendance_mode_of_member_at_date(
                attendances, ShiftAttendanceMode.REGULAR, at_date
            )
        elif selection == cls.SELECTION_FLYING_MEMBERS:
            attendances = cls.filter_attendance_by_attendance_mode_of_member_at_date(
                attendances, ShiftAttendanceMode.FLYING, at_date
            )
        elif selection == cls.SELECTION_FROZEN_MEMBERS:
            attendances = cls.filter_attendance_by_attendance_mode_of_member_at_date(
                attendances, ShiftAttendanceMode.FROZEN, at_date
            )
        elif selection == cls.SELECTION_ABCD_SHIFTS:
            attendances = (
                IsShiftAttendanceFromTemplateService.annotate_shift_attendances(
                    attendances
                )
            )
            filters = {
                IsShiftAttendanceFromTemplateService.ANNOTATION_IS_FROM_ATTENDANCE_TEMPLATE: True
            }
            attendances = attendances.filter(**filters)
        elif selection == cls.SELECTION_FLYING_SHIFTS:
            attendances = (
                IsShiftAttendanceFromTemplateService.annotate_shift_attendances(
                    attendances
                )
            )
            filters = {
                IsShiftAttendanceFromTemplateService.ANNOTATION_IS_FROM_ATTENDANCE_TEMPLATE: False
            }
            attendances = attendances.filter(**filters)

        return attendances


class ShiftCancellingRateJsonView(
    LoginRequiredMixin, PermissionRequiredMixin, JSONView
):
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
            data_labels=ShiftCountByCategoryJsonView.SELECTIONS,
            y_axis_min=0,
            y_axis_max=1,
            format_ticks=FORMAT_TICKS_PERCENTAGE,
        )

    def get_and_cache_dates_from_first_shift_to_today(self):
        if self.dates_from_first_shift_to_today is None:
            self.dates_from_first_shift_to_today = (
                ShiftCountByCategoryJsonView.get_dates_from_first_shift_to_today()
            )
        return self.dates_from_first_shift_to_today

    def get_data(self):
        return [
            self.get_cancel_rate_for_selection(selection)
            for selection in ShiftCountByCategoryJsonView.SELECTIONS
        ]

    def get_cancel_rate_for_selection(self, selection: str):
        return [
            self.get_cancel_rate_for_selection_at_date(selection, at_date)
            for at_date in self.get_and_cache_dates_from_first_shift_to_today()
        ]

    @staticmethod
    def get_cancel_rate_for_selection_at_date(selection, at_date):
        attendances = (
            ShiftCountByCategoryJsonView.get_attendances_for_selection_at_date(
                selection, at_date
            )
        )

        nb_total_attendances = attendances.count()
        nb_attended = attendances.filter(state=ShiftAttendance.State.DONE).count()
        nb_not_attended = nb_total_attendances - nb_attended

        return nb_not_attended / (nb_total_attendances or 1)

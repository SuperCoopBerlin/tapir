import csv
import datetime

from chartjs.views import JSONView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from tapir.coop.models import ShareOwner, MemberStatus, ShareOwnership
from tapir.coop.services.InvestingStatusService import InvestingStatusService
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.coop.services.NumberOfSharesService import NumberOfSharesService
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.models import (
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceMode,
    ShiftUserData,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.statistics.utils import build_line_chart_data
from tapir.statistics.views import MainStatisticsView
from tapir.utils.shortcuts import (
    get_first_of_next_month,
    get_last_day_of_month,
    ensure_datetime,
)


class StatsForMarieView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = PERMISSION_COOP_MANAGE
    template_name = "statistics/stats_for_marie.html"


class NumberOfFrozenMembersPerMonthJsonView(
    LoginRequiredMixin, PermissionRequiredMixin, JSONView
):
    permission_required = PERMISSION_COOP_MANAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates_from_first_shift_to_today = None

    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=[
                date for date in self.get_and_cache_dates_from_first_frozen_to_today()
            ],
            y_axis_values=[
                self.get_data(self.get_and_cache_dates_from_first_frozen_to_today())
            ],
            data_labels=["Number of frozen members"],
        )

    def get_and_cache_dates_from_first_frozen_to_today(self):
        if self.dates_from_first_shift_to_today is None:
            self.dates_from_first_shift_to_today = (
                self.get_dates_from_first_frozen_to_today()
            )
        return self.dates_from_first_shift_to_today

    @staticmethod
    def get_dates_from_first_frozen_to_today():
        first_frozen_log = (
            UpdateShiftUserDataLogEntry.objects.filter(
                new_values__attendance_mode=ShiftAttendanceMode.FROZEN
            )
            .order_by("created_date")
            .first()
        )
        if not first_frozen_log:
            return []

        current_date = first_frozen_log.created_date.date().replace(day=1)
        end_date = timezone.now().date() + datetime.timedelta(days=1)
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        dates.append(get_last_day_of_month(timezone.now().date()))

        # we want the end of each month rather than the first of the month
        dates = [date - datetime.timedelta(days=1) for date in dates]

        # limit to 6 month to avoid time out
        dates = dates[-6:]

        return dates

    @staticmethod
    def get_data(dates):
        data = []
        for date in dates:
            active_members = ShareOwner.objects.with_status(
                MemberStatus.ACTIVE, at_datetime=date
            )
            shift_user_datas = ShiftUserData.objects.filter(
                user__share_owner__in=active_members
            )
            shift_user_datas = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_date(
                shift_user_datas, date
            )
            filter_args = {
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.FROZEN
            }
            data.append(shift_user_datas.filter(**filter_args).count())
        return data


class NumberOfFrozenMembersPerMonthCsvView(
    LoginRequiredMixin, PermissionRequiredMixin, View
):
    permission_required = PERMISSION_COOP_MANAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates_from_first_frozen_to_today = None

    def get_and_cache_dates_from_first_frozen_to_today(self):
        if self.dates_from_first_frozen_to_today is None:
            self.dates_from_first_frozen_to_today = (
                NumberOfFrozenMembersPerMonthJsonView.get_dates_from_first_frozen_to_today()
            )
        return self.dates_from_first_frozen_to_today

    def get(self, *args, **kwargs):
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="number_of_frozen_members_per_month.csv"'
            },
        )

        writer = csv.writer(response)

        dates = self.get_and_cache_dates_from_first_frozen_to_today()
        data = NumberOfFrozenMembersPerMonthJsonView.get_data(dates)

        for index, date in enumerate(dates):
            writer.writerow([date.strftime("%d/%m/%Y"), data[index]])

        return response


class NumberOfPurchasingMembersPerMonthJsonView(
    LoginRequiredMixin, PermissionRequiredMixin, JSONView
):
    permission_required = PERMISSION_COOP_MANAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates_from_first_share_to_today = None

    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=[
                date for date in self.get_and_cache_dates_from_first_share_to_today()
            ],
            y_axis_values=[
                self.get_data(self.get_and_cache_dates_from_first_share_to_today())
            ],
            data_labels=["Number of purchasing members"],
        )

    def get_and_cache_dates_from_first_share_to_today(self):
        if self.dates_from_first_share_to_today is None:
            self.dates_from_first_share_to_today = (
                self.get_dates_from_first_share_to_today()
            )
        return self.dates_from_first_share_to_today

    @staticmethod
    def get_dates_from_first_share_to_today():
        first_share = ShareOwnership.objects.order_by("start_date").first()
        if not first_share:
            return []

        current_date = first_share.start_date.replace(day=1)
        end_date = timezone.now().date() + datetime.timedelta(days=1)
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        dates.append(get_first_of_next_month(timezone.now().date()))

        # we want the end of each month rather than the first of the month
        dates = [date - datetime.timedelta(days=1) for date in dates]

        # limit to 6 month to avoid time out
        dates = dates[-6:]

        return dates

    @staticmethod
    def get_data(dates):
        data = []
        for date in dates:
            date_with_time = ensure_datetime(date)
            share_owners = (
                ShareOwner.objects.all()
                .prefetch_related("user")
                .prefetch_related("user__shift_user_data")
                .prefetch_related("share_ownerships")
            )
            share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
                share_owners, date
            )
            share_owners = MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, date
            )
            share_owners = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
                share_owners, date_with_time
            )
            share_owners = MainStatisticsView.annotate_attendance_modes(
                share_owners, date
            )

            number_of_purchasing_members_at_date = len(
                [
                    share_owner
                    for share_owner in share_owners
                    if share_owner.can_shop(date_with_time)
                ]
            )
            data.append(number_of_purchasing_members_at_date)
        return data


class NumberOfPurchasingMembersPerMonthCsvView(
    LoginRequiredMixin, PermissionRequiredMixin, View
):
    permission_required = PERMISSION_COOP_MANAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates_from_first_share_to_today = None

    def get_and_cache_dates_from_first_share_to_today(self):
        if self.dates_from_first_share_to_today is None:
            self.dates_from_first_share_to_today = (
                NumberOfPurchasingMembersPerMonthJsonView.get_dates_from_first_share_to_today()
            )
        return self.dates_from_first_share_to_today

    def get(self, *args, **kwargs):
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="number_of_purchasing_members_per_month.csv"'
            },
        )

        writer = csv.writer(response)

        dates = self.get_and_cache_dates_from_first_share_to_today()
        data = NumberOfPurchasingMembersPerMonthJsonView.get_data(dates)

        for index, date in enumerate(dates):
            writer.writerow([date.strftime("%d/%m/%Y"), data[index]])

        return response

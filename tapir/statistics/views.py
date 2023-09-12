import datetime

from chartjs.views import JSONView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from tapir import settings
from tapir.accounts.models import UpdateTapirUserLogEntry
from tapir.coop.models import ShareOwnership, ShareOwner, MemberStatus
from tapir.coop.views import ShareCountEvolutionJsonView
from tapir.core.models import FeatureFlag
from tapir.financingcampaign.models import (
    FinancingCampaign,
    FinancingSourceDatapoint,
)
from tapir.shifts.models import (
    ShiftExemption,
    ShiftUserData,
    ShiftSlotTemplate,
    ShiftAttendanceMode,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics import config
from tapir.statistics.utils import build_pie_chart_data, build_line_chart_data


class MainStatisticsView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    template_name = "statistics/main_statistics.html"

    def get_permission_required(self):
        if FeatureFlag.get_flag_value(
            config.FEATURE_FLAG_NAME_UPDATED_STATS_PAGE_09_23
        ):
            return []
        if self.request.user.get_member_number() in [78, 1199]:  # Théo & Uya
            return []
        return [settings.PERMISSION_COOP_ADMIN]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data[
            "number_of_members_now"
        ] = MemberCountEvolutionJsonView.get_number_of_members_at_date(
            timezone.now().date()
        )
        context_data["number_of_abcd_slots"] = ShiftSlotTemplate.objects.count()
        context_data[
            "active_members_for_frozen_stats"
        ] = FrozenMembersJsonView.get_relevant_members().count()
        context_data["campaigns"] = FinancingCampaign.objects.active_temporal()

        return context_data


class CacheDatesFromFirstShareToTodayMixin:
    def __init__(self):
        super().__init__()
        self.dates_from_first_share_to_today = None

    def get_and_cache_dates_from_first_share_to_today(self):
        if self.dates_from_first_share_to_today is None:
            self.dates_from_first_share_to_today = (
                ShareCountEvolutionJsonView.get_dates_from_first_share_to_today()
            )
        return self.dates_from_first_share_to_today


class MemberCountEvolutionJsonView(CacheDatesFromFirstShareToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=self.get_and_cache_dates_from_first_share_to_today(),
            y_axis_values=[self.get_number_of_members_per_month()],
            data_labels=[_("Total number of members")],
        )

    @staticmethod
    def get_number_of_members_at_date(date: datetime.date):
        active_ownerships = ShareOwnership.objects.active_temporal(date)
        return (
            ShareOwner.objects.filter(share_ownerships__in=active_ownerships)
            .distinct()
            .count()
        )

    def get_number_of_members_per_month(self):
        number_of_members = []

        for date in self.get_and_cache_dates_from_first_share_to_today():
            number_of_members.append(self.get_number_of_members_at_date(date))

        return number_of_members


class NewMembersPerMonthJsonView(CacheDatesFromFirstShareToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        dates = self.get_and_cache_dates_from_first_share_to_today()
        data = [
            MemberCountEvolutionJsonView.get_number_of_members_at_date(date)
            - MemberCountEvolutionJsonView.get_number_of_members_at_date(
                dates[index - 1]
            )
            if index
            else 0
            for index, date in enumerate(dates)
        ]
        context_data = {
            "type": "bar",
            "data": {
                "labels": self.get_and_cache_dates_from_first_share_to_today(),
                "datasets": [
                    {
                        "label": _("New members"),
                        "data": data,
                    }
                ],
            },
        }
        return context_data


class PurchasingMembersJsonView(JSONView):
    TARGET_NUMBER_OF_PURCHASING_MEMBERS = 1140

    def get_context_data(self, **kwargs):
        number_of_purchasing_members = len(
            [
                share_owner
                for share_owner in ShareOwner.objects.all()
                .prefetch_related("user")
                .prefetch_related("user__shift_user_data")
                .prefetch_related("share_ownerships")
                if share_owner.can_shop()
            ]
        )

        # rough estimate, TODO update when the paused status arrives
        members_that_should_be_paused_instead_of_exempted = round(
            ShiftExemption.objects.active_temporal().count() / 2
        )
        number_of_purchasing_members -= (
            members_that_should_be_paused_instead_of_exempted
        )

        return build_pie_chart_data(
            labels=[
                _("Current number of purchasing members"),
                _("Missing number of purchasing members"),
            ],
            data=[
                number_of_purchasing_members,
                self.TARGET_NUMBER_OF_PURCHASING_MEMBERS - number_of_purchasing_members,
            ],
        )


class WorkingMembersJsonView(JSONView):
    def get_context_data(self, **kwargs):
        number_of_working_members = len(
            [
                shift_user_data
                for shift_user_data in ShiftUserData.objects.all()
                .prefetch_related("user")
                .prefetch_related("user__share_owner")
                .prefetch_related("user__share_owner__share_ownerships")
                .prefetch_related("shift_exemptions")
                if ShiftExpectationService.is_member_expected_to_do_shifts(
                    shift_user_data
                )
            ]
        )

        return build_pie_chart_data(
            labels=[
                _("Current number of working members"),
                _("Missing number of working members"),
            ],
            data=[
                number_of_working_members,
                ShiftSlotTemplate.objects.count() - number_of_working_members,
            ],
        )


class FrozenMembersJsonView(JSONView):
    def get_context_data(self, **kwargs):
        relevant_members = self.get_relevant_members()
        frozen_members_count = relevant_members.filter(
            user__shift_user_data__attendance_mode=ShiftAttendanceMode.FROZEN
        ).count()
        not_frozen_members_count = relevant_members.count() - frozen_members_count

        return build_pie_chart_data(
            labels=[_("Active members"), _("Frozen members")],
            data=[not_frozen_members_count, frozen_members_count],
        )

    @staticmethod
    def get_relevant_members():
        return ShareOwner.objects.with_status(MemberStatus.ACTIVE).filter(
            user__isnull=False
        )


class CoPurchasersJsonView(CacheDatesFromFirstShareToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=self.get_dates(),
            y_axis_values=[self.get_percentage_of_co_purchasers_per_month()],
            data_labels=[
                _(
                    "Percentage of members with a co-purchaser relative to the number of active members"
                )
            ],
            y_axis_max=100,
        )

    def get_dates(self):
        first_update = (
            UpdateTapirUserLogEntry.objects.filter(
                new_values__co_purchaser__isnull=False,
            )
            .order_by("created_date")
            .first()
        )
        if first_update:
            starting_month = first_update.created_date.date()
            starting_month = starting_month.replace(day=1) - datetime.timedelta(days=1)
        else:
            starting_month = None

        return [
            date
            for date in self.get_and_cache_dates_from_first_share_to_today()
            if not starting_month or date >= starting_month
        ]

    def get_percentage_of_co_purchasers_per_month(self):
        percentage_of_co_purchasers_per_month = []

        co_purchaser_updates = (
            UpdateTapirUserLogEntry.objects.filter(
                new_values__co_purchaser__isnull=False,
            )
            .order_by("created_date")
            .prefetch_related("user")
        )

        for date in self.get_dates():
            relevant_members = (
                ShareOwner.objects.with_status(MemberStatus.ACTIVE, date)
                .prefetch_related("user")
                .filter(user__isnull=False)
                .filter(user__date_joined__lte=date)
            )

            number_of_co_purchasers_at_date = len(
                [
                    member
                    for member in relevant_members
                    if self.does_member_have_a_co_purchaser_at_date(
                        member=member,
                        date=date,
                        co_purchaser_updates=co_purchaser_updates,
                    )
                ]
            )

            percentage_of_co_purchasers_per_month.append(
                number_of_co_purchasers_at_date / relevant_members.count() * 100
                if relevant_members.count() > 0
                else 0
            )

        return percentage_of_co_purchasers_per_month

    @staticmethod
    def does_member_have_a_co_purchaser_at_date(
        member: ShareOwner, date: datetime.date, co_purchaser_updates
    ):
        has_co_purchaser = None
        for update in co_purchaser_updates:
            if update.created_date.date() < date:
                continue
            if update.user == member.user:
                old_values = update.old_values
                has_co_purchaser = (
                    "co_purchaser" in old_values.keys()
                    and old_values["co_purchaser"] != ""
                )
                break
        if has_co_purchaser is None:
            has_co_purchaser = member.user.co_purchaser != ""
        return has_co_purchaser


class FinancingCampaignJsonView(JSONView):
    def get_campaign(self):
        return get_object_or_404(FinancingCampaign, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=[date for date in self.get_dates()],
            y_axis_values=self.get_data(),
            data_labels=[
                source.name
                for source in self.get_campaign().financingsource_set.order_by("name")
            ],
            y_axis_min=0,
            y_axis_max=self.get_campaign().goal,
            stacked=True,
        )

    def get_dates(self):
        return FinancingSourceDatapoint.objects.filter(
            source__campaign=self.get_campaign()
        ).dates("date", "day")

    def get_data(self):
        return [
            self.get_source_data(source)
            for source in self.get_campaign().financingsource_set.order_by("name")
        ]

    def get_source_data(self, source):
        values = []
        for date in self.get_dates():
            datapoint = (
                FinancingSourceDatapoint.objects.filter(source=source, date__lte=date)
                .order_by("-date")
                .first()
            )
            values.append(datapoint.value if datapoint else 0)
        return values

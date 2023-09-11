import datetime

from chartjs.views import JSONView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from tapir import settings
from tapir.coop.models import ShareOwnership, ShareOwner
from tapir.coop.views import ShareCountEvolutionJsonView
from tapir.core.models import FeatureFlag
from tapir.shifts.models import ShiftExemption, ShiftUserData, ShiftSlotTemplate
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics import config


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
        context_data = {
            "type": "line",
            "data": {
                "labels": self.get_and_cache_dates_from_first_share_to_today(),
                "datasets": [
                    {
                        "label": _("Total number of members"),
                        "data": self.get_number_of_members_per_month(),
                    }
                ],
            },
        }
        return context_data

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
        members_that_should_be_paused_instead_of_exempted = (
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


def build_pie_chart_data(labels: list, data: list):
    return {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": " ",
                    "data": data,
                },
            ],
        },
    }

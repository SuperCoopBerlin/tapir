import datetime

from chartjs.views import JSONView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.management import call_command
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic import RedirectView

from tapir.accounts.models import (
    TapirUser,
    UpdateTapirUserLogEntry,
)
from tapir.coop.models import ShareOwnership, ShareOwner, MemberStatus
from tapir.coop.views import ShareCountEvolutionJsonView
from tapir.financingcampaign.models import (
    FinancingCampaign,
    FinancingSourceDatapoint,
)
from tapir.settings import PERMISSION_COOP_MANAGE, PERMISSION_ACCOUNTS_VIEW
from tapir.shifts.models import (
    ShiftUserData,
    ShiftSlotTemplate,
    ShiftAttendanceMode,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.models import (
    PurchaseBasket,
    ProcessedPurchaseFiles,
)
from tapir.statistics.utils import (
    build_pie_chart_data,
    build_line_chart_data,
    build_bar_chart_data,
)
from tapir.utils.shortcuts import get_first_of_next_month


class MainStatisticsView(LoginRequiredMixin, generic.TemplateView):
    template_name = "statistics/main_statistics.html"

    TARGET_NUMBER_OF_PURCHASING_MEMBERS = 1140

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data[
            "number_of_members_now"
        ] = MemberCountEvolutionJsonView.get_number_of_members_at_date(
            timezone.now().date()
        )
        context_data["campaigns"] = FinancingCampaign.objects.active_temporal()
        context_data["extra_shares"] = self.get_extra_shares_count()
        context_data["purchasing_members"] = self.get_purchasing_members_context()
        context_data["working_members"] = self.get_working_members_context()
        context_data["target_average_monthly_basket"] = 225

        return context_data

    def get_purchasing_members_context(self):
        current_number_of_purchasing_members = len(
            [
                share_owner
                for share_owner in ShareOwner.objects.all()
                .prefetch_related("user")
                .prefetch_related("user__shift_user_data")
                .prefetch_related("share_ownerships")
                if share_owner.can_shop()
            ]
        )

        context = dict()
        context["target_count"] = self.TARGET_NUMBER_OF_PURCHASING_MEMBERS
        context["current_count"] = current_number_of_purchasing_members
        context["missing_count"] = (
            self.TARGET_NUMBER_OF_PURCHASING_MEMBERS
            - current_number_of_purchasing_members
        )
        context["progress"] = round(
            100
            * current_number_of_purchasing_members
            / self.TARGET_NUMBER_OF_PURCHASING_MEMBERS
        )
        context["missing_progress"] = 100 - context["progress"]

        return context

    @staticmethod
    def get_working_members_context():
        current_number_of_working_members = len(
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

        context = dict()
        context["target_count"] = ShiftSlotTemplate.objects.count()
        context["current_count"] = current_number_of_working_members
        context["missing_count"] = context["target_count"] - context["current_count"]
        context["progress"] = round(
            100 * context["current_count"] / context["target_count"]
        )
        context["missing_progress"] = 100 - context["progress"]
        return context

    @staticmethod
    def get_extra_shares_count():
        threshold_date = datetime.date(day=12, month=9, year=2023)
        first_shares = [
            share_owner.get_oldest_active_share_ownership().id
            for share_owner in ShareOwner.objects.all()
            if share_owner.get_oldest_active_share_ownership() is not None
        ]

        return (
            ShareOwnership.objects.filter(start_date__gte=threshold_date)
            .exclude(id__in=first_shares)
            .active_temporal()
            .count()
        )


def get_average_monthly_basket(baskets):
    baskets = baskets.order_by("purchase_date")
    if not baskets.first():
        return 0

    days_since_first_purchase = (
        timezone.now().date() - baskets.first().purchase_date.date()
    ).days
    average_days_per_month = 365.25 / 12
    months_since_first_purchase = days_since_first_purchase / average_days_per_month
    return (
        baskets.aggregate(total_paid=Sum("gross_amount"))["total_paid"]
        / months_since_first_purchase
    )


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


class BasketSumEvolutionJsonView(LoginRequiredMixin, PermissionRequiredMixin, JSONView):
    def get_permission_required(self):
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return [PERMISSION_ACCOUNTS_VIEW]

    def get_context_data(self, **kwargs):
        tapir_user = get_object_or_404(TapirUser, pk=(self.kwargs["pk"]))

        user_purchases = (
            PurchaseBasket.objects.filter(tapir_user=tapir_user)
            .annotate(month=TruncMonth("purchase_date"))
            .values("month")
            .annotate(average_gross_amount=Sum("gross_amount"))
            .order_by("month")
        )

        months = self.get_months(user_purchases)

        return build_bar_chart_data(
            data=self.get_sums_per_month(user_purchases, months),
            labels=months,
            label=_("Total spends per month"),
        )

    @staticmethod
    def get_months(user_purchases):
        if len(user_purchases) == 0:
            return []

        months = []
        now = timezone.now().date().replace(day=1)

        month = user_purchases[0]["month"].date()
        months.append(month.strftime("%Y-%m"))

        while month < now:
            month = get_first_of_next_month(month)
            months.append(month.strftime("%Y-%m"))

        return months

    @staticmethod
    def get_sums_per_month(purchases_query_set, months):
        if len(purchases_query_set) == 0:
            return []

        prices = []
        purchases_dict = {
            entry["month"].strftime("%Y-%m"): entry["average_gross_amount"]
            for entry in purchases_query_set
        }
        for month in months:
            prices.append(purchases_dict.get(month, 0))

        return prices


class FrozenMembersJsonView(JSONView):
    def get_context_data(self, **kwargs):
        relevant_members = self.get_relevant_members()
        frozen_members_count = relevant_members.filter(
            user__shift_user_data__attendance_mode=ShiftAttendanceMode.FROZEN
        ).count()
        not_frozen_members_count = relevant_members.count() - frozen_members_count

        return build_pie_chart_data(
            labels=[_("Purchasing members"), _("Frozen members")],
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


class UpdatePurchaseDataManuallyView(
    LoginRequiredMixin, PermissionRequiredMixin, RedirectView
):
    permission_required = PERMISSION_COOP_MANAGE

    def get_redirect_url(self, *args, **kwargs):
        return reverse("statistics:main_statistics")

    def get(self, request, *args, **kwargs):
        try:
            ProcessedPurchaseFiles.objects.all().delete()
            call_command("process_purchase_files")
            messages.info(request, _("Purchase data updated"))
        except Exception:
            messages.error(request, "Failed to update purchase data.")
        return super().get(request, args, kwargs)

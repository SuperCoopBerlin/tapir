import datetime

from chartjs.colors import next_color, COLORS
from chartjs.views.lines import BaseLineChartView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic import TemplateView

from tapir.accounts.models import TapirUser
from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.models import (
    ShareOwner,
    MemberStatus,
    DraftUser,
    ShareOwnership,
)
from tapir.utils.shortcuts import (
    get_first_of_next_month,
)


class StatisticsView(LoginRequiredMixin, generic.TemplateView):
    template_name = "coop/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_members = ShareOwner.objects.with_status(MemberStatus.ACTIVE)
        investing_members = ShareOwner.objects.with_status(MemberStatus.INVESTING)
        context["members_count"] = active_members.count() + investing_members.count()

        context["active_members_count"] = active_members.count()
        context["investing_members_count"] = investing_members.count()
        context["active_users_count"] = TapirUser.objects.filter(
            share_owner__in=active_members
        ).count()
        context["members_missing_accounts_count"] = active_members.filter(
            user=None
        ).count()
        context["applicants_count"] = DraftUser.objects.count()

        context["shares"] = self.get_shares_context()
        context["extra_shares"] = self.get_extra_shares_context()

        return context

    @staticmethod
    def get_shares_context():
        context = dict()
        context["nb_share_ownerships_now"] = ShareOwnership.objects.active_temporal(
            timezone.now()
        ).count()
        start_date = ShareOwnership.objects.order_by("start_date").first().start_date
        start_date = datetime.date(day=1, month=start_date.month, year=start_date.year)

        nb_months_since_start = (
            (datetime.date.today().year - start_date.year) * 12
            + datetime.date.today().month
            - start_date.month
        )
        context["average_shares_per_month"] = "{:.2f}".format(
            context["nb_share_ownerships_now"] / nb_months_since_start
        )
        context["start_date"] = start_date

        return context

    def get_extra_shares_context(self):
        context = dict()
        threshold_date = datetime.date(day=1, month=1, year=2022)
        first_shares = [
            share_owner.get_oldest_active_share_ownership().id
            for share_owner in ShareOwner.objects.exclude(
                id__in=ShareOwner.objects.with_status(MemberStatus.SOLD)
            )
        ]
        extra_shares = (
            ShareOwnership.objects.filter(start_date__gte=threshold_date)
            .exclude(id__in=first_shares)
            .active_temporal()
        )

        context["threshold_date"] = threshold_date
        context["share_count"] = extra_shares.count()
        members_who_bought_extra_shares = ShareOwner.objects.filter(
            share_ownerships__in=extra_shares
        ).distinct()
        if self.request.user.has_perm("coop.view"):
            context["members"] = members_who_bought_extra_shares
        members_count = (
            members_who_bought_extra_shares.count()
            if members_who_bought_extra_shares.exists()
            else 1
        )
        context["average_extra_shares"] = "{:.2f}".format(
            extra_shares.count() / members_count
        )

        total_amount_paid = 0
        total_cost = 0
        paid_percentage = "0%"
        if extra_shares.exists():
            total_amount_paid = extra_shares.aggregate(Sum("amount_paid"))[
                "amount_paid__sum"
            ]
            total_cost = extra_shares.count() * COOP_SHARE_PRICE
            paid_percentage = "{:.0%}".format(total_amount_paid / total_cost)

        context["total_amount_paid"] = total_amount_paid
        context["total_cost"] = total_cost
        context["paid_percentage"] = paid_percentage

        return context


class MemberCountEvolutionJsonView(BaseLineChartView):
    dates_from_first_share_to_today = None

    def get_labels(self):
        return self.get_and_cache_dates_from_first_share_to_today()

    def get_providers(self):
        return [_("All members"), _("Active"), _("Active with account")]

    def get_data(self):
        all_members_counts = []
        active_members_counts = []
        active_members_with_account_counts = []

        for date in self.get_and_cache_dates_from_first_share_to_today():
            shares_active_at_date = ShareOwnership.objects.active_temporal(date)
            members = ShareOwner.objects.filter(
                share_ownerships__in=shares_active_at_date
            ).distinct()
            all_members_counts.append(members.count())

            active_members = members.with_status(MemberStatus.ACTIVE)
            active_members_counts.append(active_members.count())

            active_members_with_account = TapirUser.objects.filter(
                share_owner__in=active_members
            )
            active_members_with_account_counts.append(
                active_members_with_account.count()
            )

        return [
            all_members_counts,
            active_members_counts,
            active_members_with_account_counts,
        ]

    def get_and_cache_dates_from_first_share_to_today(self):
        if self.dates_from_first_share_to_today is None:
            self.dates_from_first_share_to_today = (
                ShareCountEvolutionJsonView.get_dates_from_first_share_to_today()
            )
        return self.dates_from_first_share_to_today


class ShareCountEvolutionJsonView(BaseLineChartView):
    dates_from_first_share_to_today = None

    def get_labels(self):
        return self.get_and_cache_dates_from_first_share_to_today()

    def get_providers(self):
        return [_("Number of shares")]

    def get_data(self):
        return [
            [
                ShareOwnership.objects.active_temporal(date).count()
                for date in self.get_and_cache_dates_from_first_share_to_today()
            ]
        ]

    def get_colors(self):
        return next_color(COLORS[1:])

    def get_and_cache_dates_from_first_share_to_today(self):
        if self.dates_from_first_share_to_today is None:
            self.dates_from_first_share_to_today = (
                self.get_dates_from_first_share_to_today()
            )
        return self.dates_from_first_share_to_today

    @staticmethod
    def get_dates_from_first_share_to_today():
        first_share_ownership = ShareOwnership.objects.order_by("start_date").first()
        if not first_share_ownership:
            return []

        current_date = first_share_ownership.start_date.replace(day=1)
        end_date = datetime.date.today()
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        return dates


class MemberAgeDistributionJsonView(BaseLineChartView):
    age_to_number_of_members_map = None

    def get_labels(self):
        return list(self.get_age_distribution().keys())

    def get_providers(self):
        return [_("Number of members (X-axis) by age (Y-axis)")]

    def get_data(self):
        return [list(self.get_age_distribution().values())]

    def get_colors(self):
        return next_color(COLORS[1:])

    def get_age_distribution(self) -> dict:
        if self.age_to_number_of_members_map is not None:
            return self.age_to_number_of_members_map

        self.age_to_number_of_members_map = {}
        today = timezone.now().date()
        for share_owner in ShareOwner.objects.exclude(is_company=True).exclude(
            id__in=ShareOwner.objects.with_status(MemberStatus.SOLD)
        ):
            birthdate = share_owner.get_info().birthdate
            if not birthdate:
                continue
            age = (
                today.year
                - birthdate.year
                - ((today.month, today.day) < (birthdate.month, birthdate.day))
            )
            if age not in self.age_to_number_of_members_map.keys():
                self.age_to_number_of_members_map[age] = 0
            self.age_to_number_of_members_map[age] += 1

        self.age_to_number_of_members_map = dict(
            sorted(self.age_to_number_of_members_map.items())
        )

        return self.age_to_number_of_members_map


class AboutView(TemplateView):
    template_name = "coop/about.html"

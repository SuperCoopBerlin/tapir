import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
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
    get_first_of_previous_first_day_of_month,
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
        context["members_count_evolution"] = self.get_evolution_of_members_count()

        return context

    @staticmethod
    def get_evolution_of_members_count():
        first_share_ownership = ShareOwnership.objects.order_by("start_date").first()
        if not first_share_ownership:
            return None

        start_date = first_share_ownership.start_date.replace(day=1)
        current_date = datetime.date.today()
        all_members_evolution = dict()
        active_members_evolution = dict()
        while current_date >= start_date:
            shares_active_at_date = ShareOwnership.objects.active_temporal(current_date)
            members = ShareOwner.objects.filter(
                share_ownerships__in=shares_active_at_date
            ).distinct()
            all_members_evolution[current_date] = members.count()
            active_members_evolution[current_date] = members.with_status(
                MemberStatus.ACTIVE
            ).count()
            current_date = get_first_of_previous_first_day_of_month(current_date)

        context = dict()
        context["all_members_evolution"] = all_members_evolution
        context["active_members_evolution"] = active_members_evolution
        return context

    @staticmethod
    def get_shares_context():
        context = dict()
        context["nb_share_ownerships_now"] = ShareOwnership.objects.active_temporal(
            timezone.now()
        ).count()
        start_date = ShareOwnership.objects.order_by("start_date").first().start_date
        start_date = datetime.date(day=1, month=start_date.month, year=start_date.year)
        end_date = timezone.now().date()
        end_date = datetime.date(day=1, month=end_date.month, year=end_date.year)
        context["nb_shares_by_month"] = dict()
        current_date = end_date
        while current_date >= start_date:
            context["nb_shares_by_month"][
                current_date
            ] = ShareOwnership.objects.active_temporal(current_date).count()
            current_date = get_first_of_previous_first_day_of_month(current_date)

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


class AboutView(LoginRequiredMixin, TemplateView):
    template_name = "coop/about.html"

import datetime

from django.db.models import Sum
from django.utils import timezone

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.models import (
    ShiftUserData,
)
from tapir.utils.shortcuts import get_first_of_next_month


class TempCommand:
    help = "Temp command do not commit"

    def handle(self, *args, **options):
        date = timezone.now().replace(day=1, month=9, year=2021)
        counts_per_date = {}
        print("date;users_with_minus_5_or_less;active_members_with_tapir_account")
        while date <= timezone.now().replace(day=30, month=6, year=2023):
            date = self.get_last_day_of_month(date)
            counts_per_date[date] = 0
            for shift_user_data in ShiftUserData.objects.all():
                balance = (
                    shift_user_data.user.shift_account_entries.filter(
                        date__lte=date
                    ).aggregate(balance=Sum("value"))["balance"]
                    or 0
                )
                if balance <= -5:
                    counts_per_date[date] += 1
            active_users_with_account_count = (
                ShareOwner.objects.with_status(MemberStatus.ACTIVE, date)
                .filter(user__isnull=False)
                .count()
            )
            print(
                f"{date.date()};{counts_per_date[date]};{active_users_with_account_count}"
            )
            date += datetime.timedelta(days=1)

    def get_last_day_of_month(self, date):
        return get_first_of_next_month(date) - datetime.timedelta(days=1)

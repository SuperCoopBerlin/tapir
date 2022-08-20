import datetime

from django.core.management import BaseCommand

from tapir.coop.models import (
    NewMembersAndSharesEmailRecapLogs,
    ShareOwnership,
    ShareOwner,
)


class Command(BaseCommand):
    help = "Sends email"

    def handle(self, *args, **options):
        if not ShareOwnership.objects.exists():
            return

        last_mail = NewMembersAndSharesEmailRecapLogs.objects.order_by(
            "sent_recap_up_to"
        ).last()
        if last_mail is not None:
            start_date = last_mail.sent_recap_up_to + datetime.date.today()
        else:
            start_date = (
                ShareOwnership.objects.order_by("start_date").first().start_date
            )

        # We sent the recap up to yesterday, so that the next recap includes all of today's new shares,
        # including the one that will be created today but after the email has been sent.
        end_date = datetime.date.today() - datetime.timedelta(days=1)

        self.send_recap_from_to(start_date, end_date)

    @staticmethod
    def send_recap_from_to(start_date: datetime.date, end_date: datetime.date):
        share_ownerships = ShareOwnership.objects.filter(
            start_date__gte=start_date,
            start_date__lte=end_date,
        )

        share_owners_with_new_shares_since_last_mail = ShareOwner.objects.filter(
            share_ownerships__in=share_ownerships
        ).distinct()

        new_members = []
        members_who_bought_extra_shares = []

        for share_owner in share_owners_with_new_shares_since_last_mail:
            if (
                share_owner.share_ownerships.order_by(start_date).first().start_date
                < start_date
            ):
                members_who_bought_extra_shares.append(share_owner)
            else:
                new_members.append(share_owner)

        NewMembersAndSharesEmailRecapLogs.objects.create(sent_recap_up_to=end_date)

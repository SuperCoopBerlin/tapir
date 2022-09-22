from django.core.mail import EmailMultiAlternatives
from django.core.management import BaseCommand
from django.template import loader

from tapir import settings
from tapir.coop.models import (
    ShareOwnership,
    NewMembershipsForAccountingRecap,
    ExtraSharesForAccountingRecap,
)


class Command(BaseCommand):
    help = "Sends email"

    def handle(self, *args, **options):
        if not ShareOwnership.objects.exists():
            return

        # Load all entries from DB and only use those in case another entry gets created
        # while this command gets processed.
        new_membership_entries = [
            entry for entry in NewMembershipsForAccountingRecap.objects.all()
        ]
        extra_share_entries = [
            entry for entry in ExtraSharesForAccountingRecap.objects.all()
        ]
        context = {
            "num_new_members": len(new_membership_entries),
            "total_num_shares_new_members": sum(
                [entry.number_of_shares for entry in new_membership_entries]
            ),
            "total_num_shares_existing_members": sum(
                [entry.number_of_shares for entry in extra_share_entries]
            ),
            "new_member_recap_entries": new_membership_entries,
            "extra_shares_recap_entries": extra_share_entries,
        }
        body = loader.render_to_string(
            [
                "coop/email/accounting_recap.body.html",
                "coop/email/accounting_recap.body.default.html",
            ],
            context,
        )
        subject = loader.render_to_string(
            [
                "coop/email/accounting_recap.subject.html",
                "coop/email/accounting_recap.subject.default.html",
            ],
            context,
        )

        email = EmailMultiAlternatives(
            subject="".join(subject.splitlines()),
            body=body,
            to=[settings.EMAIL_ADDRESS_ACCOUNTING],
            from_email=[settings.EMAIL_ADDRESS_MEMBER_OFFICE],
        )
        email.content_subtype = "html"
        email.send()

        for entry in new_membership_entries:
            entry.delete()
        for entry in extra_share_entries:
            entry.delete()

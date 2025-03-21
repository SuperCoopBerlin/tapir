import csv
import io

from django.utils import timezone

from tapir.coop.models import (
    ShareOwner,
)
from tapir.coop.services.investing_status_service import InvestingStatusService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.coop.services.payment_status_service import PaymentStatusService
from tapir.statistics.services.dataset_export_column_builder import (
    DatasetExportColumnBuilder,
)


class Command:
    @staticmethod
    def handle():
        reference_datetime = timezone.now().replace(
            year=2021, month=12, day=31, hour=23, minute=59, second=59
        )

        members = ShareOwner.objects.all().order_by("id")
        members = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
            members, reference_datetime
        )
        members = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                members, reference_datetime.date()
            )
        )
        members = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            members, reference_datetime.date()
        )
        members = PaymentStatusService.annotate_with_payments_at_date(
            members, reference_datetime.date()
        )

        result = io.StringIO()
        writer = csv.writer(result)
        writer.writerow(
            [
                f"Status am {reference_datetime.strftime('%d.%m.%Y')}",
                "Beitrittsdatum",
                "Mitgliedsnummer",
                "Name",
                "Anschrift",
                "Pflichtanteil (#)",
                "Weitere Anteile (#)",
                "Zahlung (in €)",
                "davon Eintrittsgeld (€)",
                "davon Geschäftsguthaben (in €)",
                f"bezahlte Geschäftsguthaben (#) am {reference_datetime.strftime('%d.%m.%Y')}",
                f"unbezahlte Geschäftsguthaben (#) am {reference_datetime.strftime('%d.%m.%Y')}",
                "Ratenzahlung",
            ]
        )

        for member in members:
            member_since = DatasetExportColumnBuilder.build_column_is_member_since(
                member, reference_datetime
            )
            if not member_since:
                continue
            member_since = member_since.strftime("%d.%m.%Y")

            writer.writerow(
                [
                    DatasetExportColumnBuilder.build_column_member_status(
                        member, reference_datetime
                    ),
                    member_since,
                    DatasetExportColumnBuilder.build_column_member_number(member),
                    DatasetExportColumnBuilder.build_column_legal_name(member),
                    DatasetExportColumnBuilder.build_column_full_address(member),
                    DatasetExportColumnBuilder.build_column_compulsory_share(
                        member, reference_datetime
                    ),
                    DatasetExportColumnBuilder.build_column_additional_shares(
                        member, reference_datetime
                    ),
                    DatasetExportColumnBuilder.build_column_currently_paid(
                        member, reference_datetime
                    ),
                    DatasetExportColumnBuilder.build_column_amount_paid_for_entry_fee(
                        member, reference_datetime
                    ),
                    DatasetExportColumnBuilder.build_column_amount_paid_for_shares(
                        member, reference_datetime
                    ),
                    DatasetExportColumnBuilder.build_column_number_of_paid_shares(
                        member, reference_datetime
                    ),
                    DatasetExportColumnBuilder.build_column_number_of_unpaid_shares(
                        member, reference_datetime
                    ),
                    (
                        "ja"
                        if DatasetExportColumnBuilder.build_column_ratenzahlung(member)
                        else "nein"
                    ),
                ]
            )

        print(result.getvalue())


Command.handle()

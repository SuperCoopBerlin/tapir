import csv

from django.core.management import BaseCommand

from tapir.accounts.models import TapirUser
from tapir.settings import GROUP_VORSTAND
from tapir.utils.shortcuts import (
    send_file_to_storage_server,
)
from tapir.utils.user_utils import UserUtils


class Command(BaseCommand):
    help = "Updates the file containing the list of users that allowed purchase tracking and synchronizes it with the BioOffice server."
    FILE_NAME = "members-current.csv"

    def handle(self, *args, **options):
        self.write_users_to_file()
        send_file_to_storage_server(self.FILE_NAME, "u326634-sub4")

    @classmethod
    def write_users_to_file(cls):
        with open(cls.FILE_NAME, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "AdressID",  # Must be exactly 12 characters long and start with a 2. Fill with 0
                    "Nachname",
                    "Vorname",
                    "RabattN",
                    "Strasse",
                    "PLZ",
                    "Ort",
                    "eMail",
                ]
            )

            for user in TapirUser.objects.filter(allows_purchase_tracking=True):
                writer.writerow(
                    [
                        user.share_owner.get_id_for_biooffice(),
                        user.last_name,
                        UserUtils.build_display_name(
                            user, UserUtils.DISPLAY_NAME_TYPE_SHORT
                        ),
                        18 if user.is_in_group(GROUP_VORSTAND) else 0,
                        UserUtils.get_full_street(user.street, user.street_2),
                        user.postcode,
                        user.city,
                        user.email,
                    ]
                )

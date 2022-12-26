import csv

from django.core.management import BaseCommand

from tapir.accounts.models import TapirUser
from tapir.settings import GROUP_VORSTAND
from tapir.utils.user_utils import UserUtils


class Command(BaseCommand):
    help = "Updates the file containing the list of users that allowed purchase tracking and synchronizes it with the BioOffice server."

    def handle(self, *args, **options):
        self.write_users_to_file()
        self.send_file_to_server()

    @staticmethod
    def write_users_to_file():
        with open("purchase_tracking_list.csv", "w", newline="") as csvfile:
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
                        "2" + "{:0>11}".format(user.share_owner.id),
                        user.last_name,
                        user.first_name,
                        18 if user.is_in_group(GROUP_VORSTAND) else 0,
                        UserUtils.get_full_street(user.street, user.street_2),
                        user.postcode,
                        user.city,
                        user.email,
                    ]
                )

    @staticmethod
    def send_file_to_server():
        pass

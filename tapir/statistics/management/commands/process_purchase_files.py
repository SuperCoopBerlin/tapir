import csv
import datetime
import fnmatch
import io
from typing import Dict

import environ
import paramiko
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from fabric import Connection
from paramiko.sftp_file import SFTPFile

from tapir.accounts.models import TapirUser
from tapir.statistics.models import ProcessedPurchaseFiles, PurchaseBasket
from tapir.utils.shortcuts import get_timezone_aware_datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        env = environ.Env()
        private_key = paramiko.RSAKey.from_private_key(
            io.StringIO(env("TAPIR_SSH_KEY_PRIVATE"))
        )
        connection = Connection(
            host="u326634-sub6.your-storagebox.de",
            user="u326634-sub6",
            connect_kwargs={"pkey": private_key},
        )
        sftp_client = connection.sftp()
        already_processed_files = ProcessedPurchaseFiles.objects.all().values_list(
            "file_name", flat=True
        )
        files_on_server = fnmatch.filter(
            sftp_client.listdir(), "Statistics_Members_*.csv"
        )
        for file_name in [
            file_name
            for file_name in files_on_server
            if file_name not in already_processed_files
        ]:
            self.process_file(sftp_client.open(file_name), file_name)

    @classmethod
    @transaction.atomic
    def process_file(cls, file: SFTPFile, file_name: str):
        file.prefetch()
        source_file = ProcessedPurchaseFiles.objects.create(
            file_name=file_name[: ProcessedPurchaseFiles.MAX_FILE_NAME_LENGTH],
            processed_on=timezone.now(),
        )

        purchase_baskets = []
        for row in csv.DictReader(file, delimiter=",", quotechar='"'):
            row: Dict
            if row["Kunde"].isnumeric() and not row["Kunde"].startswith("299"):
                continue
            purchase_date = get_timezone_aware_datetime(
                date=datetime.datetime.strptime(row["Datum"], "%Y-%m-%d").date(),
                time=datetime.datetime.strptime(row["Zeit"], "%H:%M:%S").time(),
            )

            tapir_user = (
                TapirUser.objects.filter(share_owner__id=int(row["Kunde"][3:])).first()
                if row["Kunde"].isnumeric() and len(row["Kunde"]) > 3
                else None
            )
            purchase_basket = PurchaseBasket(
                source_file=source_file,
                purchase_date=purchase_date,
                cashier=row["cKasse"],
                purchase_counter=row["Bon"],
                tapir_user=tapir_user,
                gross_amount=cls.parse_german_number(row["VKBrutto_SUM"]),
                first_net_amount=cls.parse_german_number(row["VKNetto_SUM"]),
                second_net_amount=cls.parse_german_number(row["EKNetto_SUM"]),
                discount=cls.parse_german_number(row["Rabatt_SUM"]),
            )
            purchase_baskets.append(purchase_basket)

        PurchaseBasket.objects.bulk_create(purchase_baskets)

    @staticmethod
    def parse_german_number(string: str) -> float:
        return float(string.replace(",", "."))

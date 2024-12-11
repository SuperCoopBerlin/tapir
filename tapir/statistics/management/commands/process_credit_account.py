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
from tapir.statistics.models import ProcessedCreditFiles, CreditAccount
from tapir.utils.shortcuts import get_timezone_aware_datetime
from tapir.statistics.management.commands.process_purchase_files import (
    Command as ProcessPurchaseFilesCommand,
)


class Command(BaseCommand):
    help = "Display the credit account of a tapir user."

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
        already_processed_files = ProcessedCreditFiles.objects.all().values_list(
            "file_name", flat=True
        )
        files_on_server = fnmatch.filter(sftp_client.listdir(), "Accounts_*.csv")
        for file_name in [
            file_name
            for file_name in files_on_server
            if file_name not in already_processed_files
        ]:
            self.process_file(sftp_client.open(files_on_server.first()), file_name)

    @classmethod
    @transaction.atomic
    def process_file(cls, file: SFTPFile, file_name: str):
        file.prefetch()
        source_file = ProcessedCreditFiles.objects.create(
            file_name=file_name[: ProcessedCreditFiles.MAX_FILE_NAME_LENGTH],
            processed_on=timezone.now(),
        )
        for row in csv.DictReader(file, delimiter=",", quotechar='"'):
            row: Dict
            if row["ID"].isnumeric() and not row["ID"].startswith("299"):
                continue
            credit_date = get_timezone_aware_datetime(
                date=datetime.datetime.strptime(row["Datum"], "%Y-%m-%d").date(),
                time=datetime.datetime.strptime(row["Zeit"], "%H:%M:%S").time(),
            )
            tapir_user = (
                TapirUser.objects.filter(share_owner__id=int(row["ID"][3:])).first()
                if row["ID"].isnumeric() and len(row["ID"]) > 3
                else None
            )
            CreditAccount.objects.create(
                source_file=source_file,
                credit_date=credit_date,
                credit_amount=ProcessPurchaseFilesCommand.parse_german_number(
                    row["Betrag"]
                ),
                credit_counter=row["Bon"],
                cashier=row["Kasse"],
                info=row["Info"],
                tapir_user=tapir_user,
            )

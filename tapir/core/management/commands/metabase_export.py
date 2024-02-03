import os

import environ
from django.core.management.base import BaseCommand

from tapir.utils.shortcuts import (
    send_file_to_storage_server,
)


class Command(BaseCommand):
    help = (
        "Exports all the models to CSV files and sends them to our storage box. "
        "Those files will then be imported by our metabase instance."
    )

    exported_tables = [
        "accounts_tapiruser",
        "accounts_updatetapiruserlogentry",
        "coop_createpaymentlogentry",
        "coop_createshareownershipslogentry",
        "coop_deleteshareownershiplogentry",
        "coop_draftuser",
        "coop_extrasharesforaccountingrecap",
        "coop_incomingpayment",
        "coop_membershippause",
        "coop_membershippausecreatedlogentry",
        "coop_membershippauseupdatedlogentry",
        "coop_newmembershipsforaccountingrecap",
        "coop_shareowner",
        "coop_shareownership",
        "coop_updateshareownerlogentry",
        "coop_updateshareownershiplogentry",
        "shifts_createexemptionlogentry",
        "shifts_createshiftattendancelogentry",
        "shifts_createshiftattendancetemplatelogentry",
        "shifts_deleteshiftattendancetemplatelogentry",
        "shifts_shift",
        "shifts_shiftaccountentry",
        "shifts_shiftattendance",
        "shifts_shiftattendancetakenoverlogentry",
        "shifts_shiftattendancetemplate",
        "shifts_shiftcycleentry",
        "shifts_shiftexemption",
        "shifts_shiftslot",
        "shifts_shiftslottemplate",
        "shifts_shifttemplate",
        "shifts_shifttemplategroup",
        "shifts_shiftuserdata",
        "shifts_solidarityshift",
        "shifts_updateexemptionlogentry",
        "shifts_updateshiftattendancestatelogentry",
        "shifts_updateshiftuserdatalogentry",
    ]

    def handle(self, *args, **options):
        FILENAME = "tapir_dump.sql"
        env = environ.Env()
        password = env.db(default="postgresql://tapir:tapir@db:5432/tapir")["PASSWORD"]
        os.system(
            f"PGPASSWORD='{password}' pg_dump --file='{FILENAME}' --no-owner --format=custom --host=db --username=tapir tapir "
            + " ".join([f"-t {table_name}" for table_name in self.exported_tables])
        )
        send_file_to_storage_server(FILENAME, "u326634-sub7")

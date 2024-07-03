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

    def handle(self, *args, **options):
        FILENAME = "tapir_dump.sql"
        env = environ.Env()
        password = env.db(default="postgresql://tapir:tapir@db:5432/tapir")["PASSWORD"]
        os.system(
            f"PGPASSWORD='{password}' pg_dump --file='{FILENAME}' --format=custom --host=db --username=tapir tapir"
        )
        send_file_to_storage_server(FILENAME, "u326634-sub7")

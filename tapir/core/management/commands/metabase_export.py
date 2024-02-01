import csv
import shutil
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand

from tapir.accounts.models import LdapPerson, LdapGroup
from tapir.log.models import LogEntry
from tapir.utils.shortcuts import (
    send_file_to_storage_server,
)


class Command(BaseCommand):
    help = (
        "Exports all the models to CSV files and sends them to our storage box. "
        "Those files will then be imported by our metabase instance."
    )

    do_not_export = [
        ContentType,
        Group,
        LdapGroup,
        LdapPerson,
        LogEntry,
        Permission,
        Session,
        User,
    ]

    def handle(self, *args, **options):
        Path("./exports").mkdir(parents=True, exist_ok=True)
        for model in apps.get_models(include_auto_created=True, include_swapped=True):
            if model in self.do_not_export:
                continue
            self.export_model(model)

        shutil.make_archive("tapir_exports", "zip", "exports")
        send_file_to_storage_server("tapir_exports.zip", "u326634-sub7")

    @staticmethod
    def export_model(model):
        with open(f"./exports/{model.__name__}.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)

            fields = model._meta.get_fields()
            fields = [field for field in fields if hasattr(field, "value_from_object")]
            writer.writerow([field.name for field in fields])

            for instance in model.objects.order_by("pk"):
                writer.writerow([field.value_from_object(instance) for field in fields])

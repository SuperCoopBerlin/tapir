import csv

from allauth.account.models import EmailAddress
from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Exports all the models to CSV files and sends them to our storage box. "
        "Those files will then be imported by our metabase instance."
    )

    excluded = [ContentType, EmailAddress, Session, User]

    def handle(self, *args, **options):
        for model in apps.get_models(include_auto_created=True, include_swapped=True):
            if model in self.excluded:
                continue
            self.export_model(model)

    def export_model(self, model):
        print(model.__name__)
        with open(f"exports/{model.__name__}.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)

            fields = model._meta.get_fields()
            fields = [field for field in fields if not field.is_relation]
            writer.writerow([field.name for field in fields])

            for instance in model.objects.order_by("pk"):
                writer.writerow([field.value_from_object(instance) for field in fields])

from django.core.management import BaseCommand
from django.db import transaction

from tapir.configuration.models import TapirParameterDefinitionImporter


class Command(BaseCommand):
    help = "Imports the parameter definitions for all apps. It looks for instances of 'TapirParameterDefinitionImporter' and executes its 'import_definitions()' function."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Importing parameter definitions:")

        from tapir.core.parameters import ParameterCategory

        for cls in TapirParameterDefinitionImporter.__subclasses__():
            self.stdout.write(" - " + cls.__module__ + "." + cls.__name__)
            cls.import_definitions(cls)

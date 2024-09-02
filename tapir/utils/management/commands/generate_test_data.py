from django.core.management.base import BaseCommand

from tapir import settings
from tapir.utils.management.commands.generate_test_data_functions import (
    generate_test_users,
    generate_test_template_groups,
    generate_test_shift_templates,
    generate_shifts,
    clear_data,
    reset_all_test_data,
)


class Command(BaseCommand):
    help = "A list of helper function to fill the database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", help="Create 500 randomised users", action="store_true"
        )
        parser.add_argument(
            "--shift_template_groups",
            help="Create the 4 template groups (Week A,B,C,D)",
            action="store_true",
        )
        parser.add_argument(
            "--shift_templates",
            help="Fill the template groups with shift templates",
            action="store_true",
        )
        parser.add_argument(
            "--shifts",
            help="Create single shifts (not templates) in the past and coming week",
            action="store_true",
        )
        parser.add_argument(
            "--generate_shifts",
            help="Generate shift instances from shift templates",
            action="store_true",
        )
        parser.add_argument(
            "--clear",
            help="Clears most objects (except admins)",
            action="store_true",
        )
        parser.add_argument(
            "--reset_all",
            help="Runs --clear then generated test data for most models",
            action="store_true",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            print(
                "This is not a debug instance. Are you sure you want to run commands that generate test data?"
            )
            return

        if options["users"]:
            generate_test_users()
        if options["shift_template_groups"]:
            generate_test_template_groups()
        if options["shift_templates"]:
            generate_test_shift_templates()
        if options["generate_shifts"]:
            generate_shifts()
        if options["clear"]:
            clear_data()
        if options["reset_all"]:
            reset_all_test_data()

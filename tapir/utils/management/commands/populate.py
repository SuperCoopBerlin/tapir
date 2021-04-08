import sys

from django.core.management.base import BaseCommand
from tapir.utils.management.commands.populate_functions import *


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
            "--user_shifts",
            help="Register the given users to the shifts created with the 'populate shifts' command",
        )
        parser.add_argument(
            "--delete_templates", help="Delete all ShiftTemplates", action="store_true"
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
            help="Runs --clear then populate most models",
            action="store_true",
        )

    def handle(self, *args, **options):
        if options["users"]:
            populate_users()
        if options["shift_template_groups"]:
            populate_template_groups()
        if options["shift_templates"]:
            populate_shift_templates()
        if options["shifts"]:
            populate_shifts()
        if options["user_shifts"]:
            populate_user_shifts(options["user_shifts"])
        if options["delete_templates"]:
            delete_templates()
        if options["generate_shifts"]:
            generate_shifts()
        if options["clear"]:
            clear_data()
        if options["reset_all"]:
            reset_all_test_data()

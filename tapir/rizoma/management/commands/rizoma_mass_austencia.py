import csv
import datetime
from gettext import Catalog
from datetime import date

from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from icecream import ic

from tapir.accounts.models import TapirUser
from tapir.core.models import FeatureFlag
from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    ShiftSlotTemplate,
    Shift,
    ShiftAttendanceTemplate,
    ShiftUserCapability,
    ShiftUserCapabilityTranslation,
    CreateShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.utils import generate_shifts_up_to
from tapir.utils.expection_utils import TapirException
from tapir.utils.shortcuts import get_monday



class Command(BaseCommand):
    EMAIL_ROW = "Email"
    COMMENT_ROW_1 = "[CONSUMO] Motivo da dispensa"
    COMMENT_ROW_2 = "Mais Info (GT Membros)"

    def add_arguments(self, parser):
        parser.add_argument("file_name", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        today = date.today()
        with open(options["file_name"]) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                email = row[self.EMAIL_ROW]
                try:
                    user = TapirUser.objects.get(email=email)
                except TapirUser.DoesNotExist:
                    print(f"⁉️ User {email} does not exist. skipping")
                    continue
                else:
                    if not user.is_active:
                        print(f"☑️ User {user.email} is not active. skipping");
                        continue
                    user_data = user.shift_user_data;
                    if user_data.get_current_shift_exemption():
                        print(f"☑️ User {user.email} is already excempted from shifts. skipping");
                        continue
                    desc_1 = row[self.COMMENT_ROW_1]
                    desc_2 = row[self.COMMENT_ROW_2]
                    user_data.shift_exemptions.create(start_date=today, description = f"{desc_1} {desc_2}")
                    print(f"✅ User {user.email} has been excempted from shifts")

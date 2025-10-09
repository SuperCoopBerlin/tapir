import datetime

from django.core.management import BaseCommand
from django.db import transaction

from tapir.core.models import FeatureFlag
from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.rizoma.services.google_calendar_event_manager import (
    GoogleCalendarEventManager,
)
from tapir.shifts.models import ShiftAttendance


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        attendances = ShiftAttendance.objects.filter(
            slot__shift__start_time__gt=datetime.datetime.now(),
            external_event_id__isnull=True,
        )
        print("Number of events to create: " + str(attendances.count()))

        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
        ):
            print(
                "The calendar event feature is disabled, enable it in the feature flag page if desired."
            )
            return

        created = 0
        for attendance in attendances:
            GoogleCalendarEventManager.create_calendar_event(attendance)
            created += 1
            if created % 30 == 0:
                print("Created " + str(created) + " events")

        print("All events created")

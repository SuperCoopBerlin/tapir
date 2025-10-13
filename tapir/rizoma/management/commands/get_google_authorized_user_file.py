from django.conf import settings
from django.core.management import BaseCommand
from google_auth_oauthlib.flow import InstalledAppFlow

from tapir.rizoma.services.google_calendar_event_manager import (
    GoogleCalendarEventManager,
)


class Command(BaseCommand):
    # from https://developers.google.com/workspace/calendar/api/quickstart/python

    def handle(self, *args, **options):
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.PATH_TO_GOOGLE_CLIENT_SECRET_FILE,
            GoogleCalendarEventManager.SCOPES,
        )
        credentials = flow.run_local_server(port=0)
        with open(GoogleCalendarEventManager.AUTHORIZED_USER_FILE, "w") as user_file:
            user_file.write(credentials.to_json())

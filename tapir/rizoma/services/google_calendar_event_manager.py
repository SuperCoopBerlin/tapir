import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tapir.core.models import FeatureFlag
from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.shifts.models import ShiftAttendance
from tapir.utils.expection_utils import TapirException
from tapir.utils.user_utils import UserUtils
from django.conf import settings


class GoogleCalendarEventManager:
    SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]
    CALENDAR_ID = settings.GOOGLE_CALENDAR_ID
    AUTHORIZED_USER_FILE = settings.GOOGLE_AUTHORIZED_USER_FILE_PATH

    @classmethod
    def on_attendance_state_changed(cls, attendance: ShiftAttendance):
        if not attendance.is_valid():
            cls.delete_calendar_event(attendance)
            return

        if attendance.external_event_id is None:
            cls.create_calendar_event(attendance)

    @classmethod
    def delete_calendar_event(cls, attendance: ShiftAttendance):
        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
        ):
            return

        if attendance.external_event_id is None:
            return

        with cls.get_api_client() as client:
            client.events().delete(
                calendarId=cls.CALENDAR_ID,
                eventId=attendance.external_event_id,
                sendUpdates="all",
            ).execute()

        attendance.external_event_id = None
        attendance.save()

    @classmethod
    def create_calendar_event(cls, attendance: ShiftAttendance):
        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
        ):
            return

        if attendance.external_event_id is not None:
            return

        with cls.get_api_client() as client:
            result = (
                client.events()
                .insert(
                    calendarId=cls.CALENDAR_ID,
                    body=cls.build_request_body(attendance),
                )
                .execute()
            )

        attendance.external_event_id = result["id"]
        attendance.save()

    @classmethod
    def update_calendar_event(cls, attendance: ShiftAttendance):
        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
        ):
            return

        if attendance.external_event_id is None:
            return
        with cls.get_api_client() as client:
            client.events().update(
                calendarId=cls.CALENDAR_ID,
                eventId=attendance.external_event_id,
                body=cls.build_request_body(attendance),
            ).execute()

    @classmethod
    def build_request_body(cls, attendance: ShiftAttendance):
        return {
            "start": {"dateTime": attendance.slot.shift.start_time.isoformat()},
            "end": {"dateTime": attendance.slot.shift.end_time.isoformat()},
            "description": attendance.slot.shift.description,
            "summary": attendance.slot.shift.name,
            "visibility": "private",
            "attendees": [
                {
                    "displayName": attendance.user.get_display_name(
                        UserUtils.DISPLAY_NAME_TYPE_FULL
                    ),
                    "email": attendance.user.email,
                }
            ],
        }

    @classmethod
    def get_api_client(cls):
        return build("calendar", "v3", credentials=cls.get_credential())

    @classmethod
    def get_credential(cls):
        if not os.path.exists(cls.AUTHORIZED_USER_FILE):
            raise TapirException(
                "Missing google authorized user file, user the 'get_google_authorized_user_file' command from a local instance to get it."
            )

        credentials = Credentials.from_authorized_user_file(
            cls.AUTHORIZED_USER_FILE, GoogleCalendarEventManager.SCOPES
        )

        if credentials.valid:
            return credentials

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            with open(cls.AUTHORIZED_USER_FILE, "w") as user_file:
                user_file.write(credentials.to_json())
            return credentials

        raise TapirException("Invalid google token")

from django.conf import settings
from googleapiclient.discovery import build
from icecream import ic
from oauth2client.service_account import ServiceAccountCredentials

from tapir.core.models import FeatureFlag
from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.shifts.models import ShiftAttendance
from tapir.utils.expection_utils import TapirException


class GoogleCalendarEventManager:
    SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]
    CALENDAR_ID = "primary"

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

        cls.get_api_client().events().delete(
            calendarId=cls.CALENDAR_ID,
            eventId=attendance.external_event_id,
            sendUpdates=True,
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

        result = (
            cls.get_api_client()
            .events()
            .insert(
                calendarId=cls.CALENDAR_ID,
                body=cls.build_request_body(attendance),
            )
            .execute()
        )

        attendance.external_event_id = result["id"]
        attendance.save()

        ic(result)

    @classmethod
    def update_calendar_event(cls, attendance: ShiftAttendance):
        if not FeatureFlag.get_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
        ):
            return

        if attendance.external_event_id is None:
            return

        cls.get_api_client().events().update(
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
            "name": attendance.slot.shift.name,
            "visibility": "private",
        }

    @classmethod
    def get_api_client(cls):
        return build("calendar", "v3", credentials=cls.get_credential())

    @classmethod
    def get_credential(cls):
        credential = ServiceAccountCredentials.from_json_keyfile_name(
            settings.GOOGLE_CREDENTIALS_FILE, cls.SCOPES
        )

        if not credential or credential.invalid:
            raise TapirException("Unable to authenticate using service account key.")

        return credential

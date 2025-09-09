import datetime
import zoneinfo
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.rizoma.services.google_calendar_event_manager import (
    GoogleCalendarEventManager,
)
from tapir.shifts.tests.factories import ShiftSlotFactory, ShiftFactory
from tapir.utils.tests_utils import FeatureFlagTestMixin


class TestCreateCalendarEvent(FeatureFlagTestMixin, SimpleTestCase):
    @patch.object(GoogleCalendarEventManager, "get_api_client")
    def test_createCalendarEvent_featureFlagIsOff_doesNothing(
        self, mock_get_api_client: Mock
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS, False
        )
        attendance = Mock()
        attendance.external_event_id = None

        GoogleCalendarEventManager.create_calendar_event(attendance)

        mock_get_api_client.assert_not_called()
        self.assertEqual(None, attendance.external_event_id)
        attendance.save.assert_not_called()

    @patch.object(GoogleCalendarEventManager, "get_api_client")
    def test_createCalendarEvent_eventAlreadyExists_doesNothing(
        self, mock_get_api_client: Mock
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS, True
        )
        attendance = Mock()
        attendance.external_event_id = "test_id"

        GoogleCalendarEventManager.create_calendar_event(attendance)

        mock_get_api_client.assert_not_called()
        self.assertEqual("test_id", attendance.external_event_id)
        attendance.save.assert_not_called()

    @patch.object(GoogleCalendarEventManager, "get_api_client")
    def test_createCalendarEvent_eventDoesntExist_createEventAndSetExternalId(
        self, mock_get_api_client: Mock
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS, True
        )
        start_time = timezone.make_aware(
            datetime.datetime(year=2022, month=6, day=13, hour=12, minute=30),
            zoneinfo.ZoneInfo("Europe/Berlin"),
        )
        end_time = start_time + datetime.timedelta(hours=3)
        shift = ShiftFactory.build(
            start_time=start_time,
            end_time=end_time,
            description="test description",
            name="test name",
        )
        slot = ShiftSlotFactory.build(shift=shift)

        attendance = Mock()
        attendance.slot = slot
        attendance.external_event_id = None
        events_client = Mock()
        mock_get_api_client.return_value.events.return_value = events_client
        insert_api_endpoint = Mock()
        events_client.insert = insert_api_endpoint
        insert_api_endpoint.return_value.execute.return_value = {"id": "test_id"}

        GoogleCalendarEventManager.create_calendar_event(attendance)

        insert_api_endpoint.assert_called_once_with(
            calendarId="primary",
            body={
                "start": {"dateTime": "2022-06-13T12:30:00+02:00"},
                "end": {"dateTime": "2022-06-13T15:30:00+02:00"},
                "description": "test description",
                "name": "test name",
                "visibility": "private",
            },
        )
        insert_api_endpoint.return_value.execute.assert_called_once_with()
        self.assertEqual("test_id", attendance.external_event_id)
        attendance.save.assert_called_once()

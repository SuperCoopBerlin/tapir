from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.rizoma.services.google_calendar_event_manager import (
    GoogleCalendarEventManager,
)
from tapir.utils.tests_utils import FeatureFlagTestMixin


class TestDeleteCalendarEvent(FeatureFlagTestMixin, SimpleTestCase):
    @patch.object(GoogleCalendarEventManager, "get_api_client")
    def test_deleteCalendarEvent_featureFlagIsOff_doesNothing(
        self, mock_get_api_client: Mock
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS, False
        )
        attendance = Mock()
        attendance.external_event_id = "test_id"

        GoogleCalendarEventManager.delete_calendar_event(attendance)

        mock_get_api_client.assert_not_called()
        self.assertEqual("test_id", attendance.external_event_id)
        attendance.save.assert_not_called()

    @patch.object(GoogleCalendarEventManager, "get_api_client")
    def test_deleteCalendarEvent_eventDoesntExist_doesNothing(
        self, mock_get_api_client: Mock
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS, True
        )
        attendance = Mock()
        attendance.external_event_id = None

        GoogleCalendarEventManager.delete_calendar_event(attendance)

        mock_get_api_client.assert_not_called()
        self.assertEqual(None, attendance.external_event_id)
        attendance.save.assert_not_called()

    @patch.object(GoogleCalendarEventManager, "get_api_client")
    def test_deleteCalendarEvent_eventExists_deletesEventAndSetExternalIdToNone(
        self, mock_get_api_client: Mock
    ):
        self.given_feature_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS, True
        )
        attendance = Mock()
        attendance.external_event_id = "test_id"
        events_client = Mock()
        mock_get_api_client.return_value.events.return_value = events_client
        delete_api_endpoint = Mock()
        events_client.delete = delete_api_endpoint

        GoogleCalendarEventManager.delete_calendar_event(attendance)

        delete_api_endpoint.assert_called_once_with(
            calendarId="primary", eventId="test_id", sendUpdates=True
        )
        delete_api_endpoint.return_value.execute.assert_called_once_with()
        self.assertEqual(None, attendance.external_event_id)
        attendance.save.assert_called_once()

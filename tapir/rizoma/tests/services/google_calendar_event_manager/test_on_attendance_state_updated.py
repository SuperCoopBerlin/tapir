from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from tapir.rizoma.services.google_calendar_event_manager import (
    GoogleCalendarEventManager,
)


class TestOnAttendanceStateChanged(SimpleTestCase):
    @patch.object(GoogleCalendarEventManager, "delete_calendar_event")
    @patch.object(GoogleCalendarEventManager, "create_calendar_event")
    def test_onAttendanceStateChanged_attendanceIsNotValid_callsDelete(
        self, mock_create_calendar_event: Mock, mock_delete_calendar_event: Mock
    ):
        attendance = Mock()
        attendance.is_valid.return_value = False

        GoogleCalendarEventManager.on_attendance_state_changed(attendance)

        mock_create_calendar_event.assert_not_called()
        mock_delete_calendar_event.assert_called_once_with(attendance)

    @patch.object(GoogleCalendarEventManager, "delete_calendar_event")
    @patch.object(GoogleCalendarEventManager, "create_calendar_event")
    def test_onAttendanceStateChanged_attendanceIsValidButEventAlreadyExists_doNothing(
        self, mock_create_calendar_event: Mock, mock_delete_calendar_event: Mock
    ):
        attendance = Mock()
        attendance.is_valid.return_value = True
        attendance.external_event_id = "test_id"

        GoogleCalendarEventManager.on_attendance_state_changed(attendance)

        mock_create_calendar_event.assert_not_called()
        mock_delete_calendar_event.assert_not_called()

    @patch.object(GoogleCalendarEventManager, "delete_calendar_event")
    @patch.object(GoogleCalendarEventManager, "create_calendar_event")
    def test_onAttendanceStateChanged_attendanceIsValidAndEventDoesntExist_callsCreate(
        self, mock_create_calendar_event: Mock, mock_delete_calendar_event: Mock
    ):
        attendance = Mock()
        attendance.is_valid.return_value = True
        attendance.external_event_id = None

        GoogleCalendarEventManager.on_attendance_state_changed(attendance)

        mock_create_calendar_event.assert_called_once_with(attendance)
        mock_delete_calendar_event.assert_not_called()

from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.shifts.tasks import (
    send_shift_reminders,
    apply_shift_cycle_start,
    generate_shifts,
    run_freeze_checks,
)


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.shifts.tasks.call_command")
    def test_sendShiftReminders(self, mock_call_command: Mock):
        send_shift_reminders()
        mock_call_command.assert_called_once_with("send_shift_reminders")

    @patch("tapir.shifts.tasks.call_command")
    def test_applyShiftCycleStart(self, mock_call_command: Mock):
        apply_shift_cycle_start()
        mock_call_command.assert_called_once_with("apply_shift_cycle_start")

    @patch("tapir.shifts.tasks.call_command")
    def test_generateShifts(self, mock_call_command: Mock):
        generate_shifts()
        mock_call_command.assert_called_once_with("generate_shifts")

    @patch("tapir.shifts.tasks.call_command")
    def test_runFreezeChecks(self, mock_call_command: Mock):
        run_freeze_checks()
        mock_call_command.assert_called_once_with("run_freeze_checks")

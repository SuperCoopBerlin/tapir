from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.accounts.tasks import (
    update_purchase_tracking_list,
    send_create_account_reminder,
)
from tapir.coop.tasks import send_accounting_recap
from tapir.core.tasks import metabase_export
from tapir.shifts.tasks import (
    send_shift_reminders,
    apply_shift_cycle_start,
    generate_shifts,
    run_freeze_checks,
)
from tapir.statistics.tasks import process_purchase_files
from tapir.statistics.tasks import process_credit_account


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.statistics.tasks.call_command")
    def test_processPurchaseFiles(self, mock_call_command: Mock):
        process_purchase_files()
        mock_call_command.assert_called_once_with("process_purchase_files")

    def test_processCreditAccount(self, mock_call_command: Mock):
        process_credit_account()
        mock_call_command.assert_called_once_with("process_credit_account")

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


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.core.tasks.call_command")
    def test_metabaseExport(self, mock_call_command: Mock):
        metabase_export()
        mock_call_command.assert_called_once_with("metabase_export")

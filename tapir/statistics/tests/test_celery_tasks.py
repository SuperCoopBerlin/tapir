from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.statistics.tasks import process_credit_account
from tapir.statistics.tasks import process_purchase_files


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.statistics.tasks.call_command")
    def test_processPurchaseFiles(self, mock_call_command: Mock):
        process_purchase_files()
        mock_call_command.assert_called_once_with("process_purchase_files")

    @patch("tapir.statistics.tasks.call_command")
    def test_processCreditAccount(self, mock_call_command: Mock):
        process_credit_account()
        mock_call_command.assert_called_once_with("process_credit_account")

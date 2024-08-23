from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.coop.tasks import send_accounting_recap


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.coop.tasks.call_command")
    def test_sendAccountingRecap(self, mock_call_command: Mock):
        send_accounting_recap()
        mock_call_command.assert_called_once_with("send_accounting_recap")

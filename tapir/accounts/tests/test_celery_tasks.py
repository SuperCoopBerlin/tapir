from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.accounts.tasks import (
    update_purchase_tracking_list,
    send_create_account_reminder,
)


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.accounts.tasks.call_command")
    def test_updatePurchaseTrackingList(self, mock_call_command: Mock):
        update_purchase_tracking_list()
        mock_call_command.assert_called_once_with("update_purchase_tracking_list")

    @patch("tapir.accounts.tasks.call_command")
    def test_sendCreateAccountReminder(self, mock_call_command: Mock):
        send_create_account_reminder()
        mock_call_command.assert_called_once_with("send_create_account_reminder")

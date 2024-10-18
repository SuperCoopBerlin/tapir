from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.core.tasks import metabase_export


class TestCeleryTasks(SimpleTestCase):
    @patch("tapir.core.tasks.call_command")
    def test_metabaseExport(self, mock_call_command: Mock):
        metabase_export()
        mock_call_command.assert_called_once_with("metabase_export")

import datetime
from unittest.mock import Mock

from django.test import SimpleTestCase

from tapir.shifts.services.can_look_for_standin_service import CanLookForStandinService
from tapir.utils.tests_utils import mock_timezone_now


class TestCanLookForStandinService(SimpleTestCase):
    NOW = datetime.datetime(year=2024, month=7, day=8)

    def setUp(self):
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_canLookForAStandin_shiftIsInThePast_returnsFalse(self):
        slot = Mock()
        slot.shift.start_time = self.NOW - datetime.timedelta(hours=1)

        self.assertFalse(CanLookForStandinService.can_look_for_a_standin(slot))

    def test_canLookForAStandin_shiftIsInTheFuture_returnsTrue(self):
        slot = Mock()
        slot.shift.start_time = self.NOW + datetime.timedelta(hours=1)

        self.assertTrue(CanLookForStandinService.can_look_for_a_standin(slot))

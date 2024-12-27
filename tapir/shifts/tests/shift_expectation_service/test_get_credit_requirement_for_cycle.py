import datetime
from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.utils.shortcuts import get_timezone_aware_datetime
from tapir.utils.tests_utils import mock_timezone_now


class TestGetCreditRequirementForCycle(SimpleTestCase):
    NOW = datetime.datetime(year=2021, month=3, day=15)

    def setUp(self):
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    def test_getCreditRequirementForCycle_memberShouldDoShifts_returns1(
        self, mock_is_member_expected_to_do_shifts: Mock
    ):
        cycle_start_date = datetime.date(year=2024, month=6, day=1)
        shift_user_data = Mock()
        mock_is_member_expected_to_do_shifts.return_value = True

        result = ShiftExpectationService.get_credit_requirement_for_cycle(
            shift_user_data, cycle_start_date
        )

        self.assertEqual(1, result)
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data,
            get_timezone_aware_datetime(cycle_start_date, self.NOW.time()),
        )

    @patch.object(ShiftExpectationService, "is_member_expected_to_do_shifts")
    def test_getCreditRequirementForCycle_memberShouldNotDoShifts_returns0(
        self, mock_is_member_expected_to_do_shifts: Mock
    ):
        cycle_start_date = datetime.date(year=2024, month=6, day=1)
        shift_user_data = Mock()
        mock_is_member_expected_to_do_shifts.return_value = False

        result = ShiftExpectationService.get_credit_requirement_for_cycle(
            shift_user_data, cycle_start_date
        )

        self.assertEqual(0, result)
        mock_is_member_expected_to_do_shifts.assert_called_once_with(
            shift_user_data,
            get_timezone_aware_datetime(cycle_start_date, self.NOW.time()),
        )

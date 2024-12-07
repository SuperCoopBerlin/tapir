import datetime
from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService


class TestIsMemberExpectedToDoShifts(SimpleTestCase):
    @staticmethod
    def create_mock_user_that_should_do_shifts(
        mock_is_frozen_at_datetime, reference_time
    ):
        shift_user_data = Mock()

        shift_user_data.user.share_owner = Mock()
        mock_is_frozen_at_datetime.return_value = False
        shift_user_data.user.date_joined = reference_time - datetime.timedelta(days=1)
        shift_user_data.user.share_owner.is_active.return_value = True
        shift_user_data.is_currently_exempted_from_shifts.return_value = False

        return shift_user_data

    @patch.object(FrozenStatusHistoryService, "is_frozen_at_datetime")
    def test_isMemberExpectedToDoShifts_memberShouldDoShifts_returnsTrue(
        self, mock_is_frozen_at_datetime: Mock
    ):
        reference_time = datetime.datetime(year=2024, month=6, day=1)
        shift_user_data = self.create_mock_user_that_should_do_shifts(
            mock_is_frozen_at_datetime, reference_time
        )

        self.assertTrue(
            ShiftExpectationService.is_member_expected_to_do_shifts(
                shift_user_data, reference_time
            )
        )

        mock_is_frozen_at_datetime.assert_called_once_with(
            shift_user_data, reference_time
        )
        shift_user_data.user.share_owner.is_active.assert_called_once_with(
            reference_time
        )
        shift_user_data.is_currently_exempted_from_shifts.assert_called_once_with(
            reference_time.date()
        )

    @patch.object(FrozenStatusHistoryService, "is_frozen_at_datetime")
    def test_isMemberExpectedToDoShifts_noShareOwner_returnsFalse(
        self, mock_is_frozen_at_datetime: Mock
    ):
        reference_time = datetime.datetime(year=2024, month=6, day=1)
        shift_user_data = self.create_mock_user_that_should_do_shifts(
            mock_is_frozen_at_datetime, reference_time
        )
        shift_user_data.user.share_owner = None

        self.assertFalse(
            ShiftExpectationService.is_member_expected_to_do_shifts(
                shift_user_data, reference_time
            )
        )

        mock_is_frozen_at_datetime.assert_not_called()
        shift_user_data.is_currently_exempted_from_shifts.assert_not_called()

    @patch.object(FrozenStatusHistoryService, "is_frozen_at_datetime")
    def test_isMemberExpectedToDoShifts_isFrozen_returnsFalse(
        self, mock_is_frozen_at_datetime: Mock
    ):
        reference_time = datetime.datetime(year=2024, month=6, day=1)
        shift_user_data = self.create_mock_user_that_should_do_shifts(
            mock_is_frozen_at_datetime, reference_time
        )
        mock_is_frozen_at_datetime.return_value = True

        self.assertFalse(
            ShiftExpectationService.is_member_expected_to_do_shifts(
                shift_user_data, reference_time
            )
        )

        mock_is_frozen_at_datetime.assert_called_once_with(
            shift_user_data, reference_time
        )
        shift_user_data.user.share_owner.is_active.assert_not_called()
        shift_user_data.is_currently_exempted_from_shifts.assert_not_called()

    @patch.object(FrozenStatusHistoryService, "is_frozen_at_datetime")
    def test_isMemberExpectedToDoShifts_userJoinedAfterDate_returnsFalse(
        self, mock_is_frozen_at_datetime: Mock
    ):
        reference_time = datetime.datetime(year=2024, month=6, day=1)
        shift_user_data = self.create_mock_user_that_should_do_shifts(
            mock_is_frozen_at_datetime, reference_time
        )
        shift_user_data.user.date_joined = reference_time + datetime.timedelta(days=1)

        self.assertFalse(
            ShiftExpectationService.is_member_expected_to_do_shifts(
                shift_user_data, reference_time
            )
        )

        mock_is_frozen_at_datetime.assert_called_once_with(
            shift_user_data, reference_time
        )
        shift_user_data.user.share_owner.is_active.assert_not_called()
        shift_user_data.is_currently_exempted_from_shifts.assert_not_called()

    @patch.object(FrozenStatusHistoryService, "is_frozen_at_datetime")
    def test_isMemberExpectedToDoShifts_userIsNotActive_returnsFalse(
        self, mock_is_frozen_at_datetime: Mock
    ):
        reference_time = datetime.datetime(year=2024, month=6, day=1)
        shift_user_data = self.create_mock_user_that_should_do_shifts(
            mock_is_frozen_at_datetime, reference_time
        )
        shift_user_data.user.share_owner.is_active.return_value = False

        self.assertFalse(
            ShiftExpectationService.is_member_expected_to_do_shifts(
                shift_user_data, reference_time
            )
        )

        mock_is_frozen_at_datetime.assert_called_once_with(
            shift_user_data, reference_time
        )
        shift_user_data.user.share_owner.is_active.assert_called_once_with(
            reference_time
        )
        shift_user_data.is_currently_exempted_from_shifts.assert_not_called()

    @patch.object(FrozenStatusHistoryService, "is_frozen_at_datetime")
    def test_isMemberExpectedToDoShifts_userIsExempted_returnsFalse(
        self, mock_is_frozen_at_datetime: Mock
    ):
        reference_time = datetime.datetime(year=2024, month=6, day=1)
        shift_user_data = self.create_mock_user_that_should_do_shifts(
            mock_is_frozen_at_datetime, reference_time
        )
        shift_user_data.is_currently_exempted_from_shifts.return_value = True

        self.assertFalse(
            ShiftExpectationService.is_member_expected_to_do_shifts(
                shift_user_data, reference_time
            )
        )

        mock_is_frozen_at_datetime.assert_called_once_with(
            shift_user_data, reference_time
        )
        shift_user_data.user.share_owner.is_active.assert_called_once_with(
            reference_time
        )
        shift_user_data.is_currently_exempted_from_shifts.assert_called_once_with(
            reference_time.date()
        )

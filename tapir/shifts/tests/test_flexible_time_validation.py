import datetime
from unittest.mock import patch, Mock

from tapir.shifts.forms import CustomTimeCleanMixin
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestFlexibleTime(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=6, day=15, hour=12, minute=0)

    def setUp(self) -> None:
        mock_timezone_now(self, self.NOW)

    @patch.object(CustomTimeCleanMixin, "get_shift_object")
    def test_registerUserToShiftSlotForm_registerOutsideShiftTimesButShiftNotFlexible_formValid(
        self, mock_get_shift_object: Mock
    ):
        shift = ShiftFactory(
            flexible_time=False,
            start_time=self.NOW,
            end_time=self.NOW + datetime.timedelta(hours=5),
        )
        custom_time = datetime.time(hour=6, minute=0)
        mock_get_shift_object.return_value = shift
        form = CustomTimeCleanMixin(data={"custom_time": custom_time})

        self.assertTrue(form.is_valid())

    @patch.object(CustomTimeCleanMixin, "get_shift_object")
    def test_registerUserToShiftSlotForm_registerBeforeShiftTimes_formInvalid(
        self, mock_get_shift_object: Mock
    ):
        shift = ShiftFactory(
            flexible_time=True,
            start_time=self.NOW,
            end_time=self.NOW + datetime.timedelta(hours=5),
        )
        custom_time = datetime.time(hour=6, minute=0)
        mock_get_shift_object.return_value = shift
        form = CustomTimeCleanMixin(data={"custom_time": custom_time})

        self.assertFalse(form.is_valid())
        self.assertIn("custom_time", form.errors.keys())

    @patch.object(CustomTimeCleanMixin, "get_shift_object")
    def test_registerUserToShiftSlotForm_registerAfterShiftTimes_formInvalid(
        self, mock_get_shift_object: Mock
    ):
        shift = ShiftFactory(
            flexible_time=True,
            start_time=self.NOW,
            end_time=self.NOW + datetime.timedelta(hours=5),
        )
        custom_time = datetime.time(hour=18, minute=0)
        mock_get_shift_object.return_value = shift
        form = CustomTimeCleanMixin(data={"custom_time": custom_time})

        self.assertFalse(form.is_valid())
        self.assertIn("custom_time", form.errors.keys())

    @patch.object(CustomTimeCleanMixin, "get_shift_object")
    def test_registerUserToShiftSlotForm_registerWithinShiftTimes_formValid(
        self, mock_get_shift_object: Mock
    ):
        shift = ShiftFactory(
            flexible_time=True,
            start_time=self.NOW,
            end_time=self.NOW + datetime.timedelta(hours=5),
        )
        custom_time = datetime.time(hour=13, minute=0)
        mock_get_shift_object.return_value = shift
        form = CustomTimeCleanMixin(data={"custom_time": custom_time})

        self.assertTrue(form.is_valid())

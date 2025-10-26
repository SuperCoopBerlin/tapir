from datetime import datetime, date, time
from unittest.mock import patch, Mock, call

from django.urls import reverse

from tapir.shifts.models import Shift
from tapir.shifts.services.shift_cancellation_service import ShiftCancellationService
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


@patch(
    "tapir.shifts.services.shift_cancellation_service.ShiftCancellationService.cancel",
    wraps=ShiftCancellationService.cancel,
)
class TestDayShiftCancel(TapirFactoryTestBase):
    VIEW_NAME_SHIFT_DAY_CANCEL = "shifts:shift_day_cancel"
    A_CANCELLATION_REASON = "A cancellation reason"
    DAY_TO_CANCEL = "01-01-25"

    def setup_shifts(self) -> tuple[list[Shift], list[Shift]]:
        """Helper to create shifts on different days for testing."""
        date_to_cancel = datetime.strptime(self.DAY_TO_CANCEL, "%d-%m-%y").date()
        other_date = date_to_cancel.replace(day=date_to_cancel.day + 1)

        def create_shift(time_val: str, date_obj: date = date_to_cancel) -> Shift:
            time_obj = time.fromisoformat(time_val)
            return ShiftFactory.create(start_time=datetime.combine(date_obj, time_obj))

        shifts_on_day = [
            create_shift("08:00"),
            create_shift("11:00"),
            create_shift("14:00"),
            create_shift("17:00"),
            create_shift("20:00"),
        ]
        shifts_on_other_day = [
            create_shift("09:00", date_obj=other_date),
            create_shift("12:00", date_obj=other_date),
        ]
        return shifts_on_day, shifts_on_other_day

    def assert_shifts_canceled(
        self, shifts_to_check: list[Shift], should_be_cancelled: bool
    ):
        """Helper to assert whether the given shifts are cancelled or not."""
        for shift in shifts_to_check:
            shift.refresh_from_db()
            if should_be_cancelled:
                self.assertTrue(
                    shift.cancelled, "The shift should be marked as cancelled."
                )
                self.assertEqual(
                    shift.cancelled_reason,
                    self.A_CANCELLATION_REASON,
                    "The shift's cancellation reason should be set correctly.",
                )
            else:
                self.assertFalse(
                    shift.cancelled,
                    "The shift should not be marked as cancelled.",
                )
                self.assertIsNone(
                    shift.cancelled_reason,
                    "The shift's cancellation reason should not be set.",
                )

    def test_cancel_all_shifts(self, mock_cancel: Mock):
        self.login_as_member_office_user()
        shifts, _ = self.setup_shifts()

        response = self.client.post(
            reverse(self.VIEW_NAME_SHIFT_DAY_CANCEL, args=[self.DAY_TO_CANCEL]),
            {
                "cancellation_reason": self.A_CANCELLATION_REASON,
                **{f"shift_{shift.id}": True for shift in shifts},
            },
        )

        self.assertRedirects(
            response,
            reverse("shifts:calendar"),
            msg_prefix="The request should redirect to the shifts calendar",
        )

        # We we make sure that the cancellation service was called with all selected shifts
        # The logic for updating the attendance is tested in the service tests
        mock_cancel.assert_has_calls([call(shift) for shift in shifts], any_order=True)

        self.assert_shifts_canceled(shifts, should_be_cancelled=True)

    def test_does_not_cancel_unselected_shifts(self, mock_cancel: Mock):
        self.login_as_member_office_user()
        shifts, shifts_on_another_day = self.setup_shifts()

        shifts_to_cancel = shifts[:3]  # Select only first three shifts
        shifts_to_keep = shifts[3:]  # Keep the rest

        response = self.client.post(
            reverse(self.VIEW_NAME_SHIFT_DAY_CANCEL, args=[self.DAY_TO_CANCEL]),
            {
                "cancellation_reason": self.A_CANCELLATION_REASON,
                **{f"shift_{shift.id}": True for shift in shifts_to_cancel},
                **{f"shift_{shift.id}": False for shift in shifts_to_keep},
            },
        )

        self.assertRedirects(
            response,
            reverse("shifts:calendar"),
            msg_prefix="The request should redirect to the shifts calendar",
        )

        # We we make sure that the cancellation service was called with all selected shifts
        # The logic for updating the attendance is tested in the service tests
        mock_cancel.assert_has_calls(
            [call(shift) for shift in shifts_to_cancel], any_order=True
        )
        self.assertEqual(
            mock_cancel.call_count,
            len(shifts_to_cancel),
            "The cancellation service should only be called for the selected shifts.",
        )

        self.assert_shifts_canceled(shifts_to_cancel, should_be_cancelled=True)
        self.assert_shifts_canceled(shifts_to_keep, should_be_cancelled=False)
        self.assert_shifts_canceled(shifts_on_another_day, should_be_cancelled=False)

    def test_does_not_cancel_already_cancelled_shifts(self, mock_cancel: Mock):
        self.login_as_member_office_user()
        shifts, _ = self.setup_shifts()

        # Pre-cancel one shift
        shift_to_pre_cancel = shifts[2]
        shift_to_pre_cancel.cancelled_reason = "Pre-cancelled for testing"
        ShiftCancellationService.cancel(shift_to_pre_cancel)
        mock_cancel.reset_mock()  # don't count this call in the test

        response = self.client.post(
            reverse(self.VIEW_NAME_SHIFT_DAY_CANCEL, args=[self.DAY_TO_CANCEL]),
            {
                "cancellation_reason": self.A_CANCELLATION_REASON,
                **{f"shift_{shift.id}": True for shift in shifts},
            },
        )

        self.assertRedirects(
            response,
            reverse("shifts:calendar"),
            msg_prefix="The request should redirect to the shifts calendar",
        )

        # We we make sure that the cancellation service was called with all selected shifts
        # The logic for updating the attendance is tested in the service tests
        mock_cancel.assert_has_calls(
            [call(shift) for shift in shifts if not shift.cancelled_reason],
            any_order=True,
        )

        self.assert_shifts_canceled(
            [shift for shift in shifts if not shift.cancelled_reason],
            should_be_cancelled=True,
        )
        self.assertEqual(
            mock_cancel.call_count,
            len(shifts) - 1,
            "The cancellation service should not be called for already cancelled shifts.",
        )

        # Ensure the pre-cancelled shift remains cancelled with its original reason
        shift_to_pre_cancel.refresh_from_db()
        self.assertTrue(
            shift_to_pre_cancel.cancelled,
            "The pre-cancelled shift should remain marked as cancelled.",
        )
        self.assertEqual(
            shift_to_pre_cancel.cancelled_reason,
            "Pre-cancelled for testing",
            "The pre-cancelled shift's cancellation reason should remain unchanged.",
        )

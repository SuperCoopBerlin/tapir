from unittest.mock import patch, Mock

from django.urls import reverse

from tapir.shifts.models import Shift
from tapir.shifts.services.shift_cancellation_service import ShiftCancellationService
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCancel(TapirFactoryTestBase):
    VIEW_NAME_CANCEL_SHIFT = "shifts:cancel_shift"
    A_CANCELLATION_REASON = "A cancellation reason"

    @patch(
        "tapir.shifts.services.shift_cancellation_service.ShiftCancellationService.cancel",
        wraps=ShiftCancellationService.cancel,
    )
    def test_shift_is_cancelled_via_cancellation_service(self, mock_cancel: Mock):
        self.login_as_member_office_user()
        shift = ShiftFactory.create()

        response = self.client.post(
            reverse(self.VIEW_NAME_CANCEL_SHIFT, args=[shift.id]),
            {"cancelled_reason": self.A_CANCELLATION_REASON},
        )

        self.assertRedirects(
            response,
            shift.get_absolute_url(),
            msg_prefix="The request should redirect to the shift's page.",
        )

        # We we make sure that the cancellation service was called
        # The logic for updating the attendance is tested in the service tests
        mock_cancel.assert_called_once_with(shift)

        # Assert that the shift is cancelled now
        updated_shift = Shift.objects.get(id=shift.id)
        self.assertTrue(
            updated_shift.cancelled, "The shift should be marked as cancelled."
        )
        self.assertEqual(
            updated_shift.cancelled_reason,
            self.A_CANCELLATION_REASON,
            "The shift's cancellation reason should be set correctly.",
        )

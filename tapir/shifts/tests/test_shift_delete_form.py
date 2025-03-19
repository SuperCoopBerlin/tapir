from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.forms import ShiftDeleteForm
from tapir.shifts.models import ShiftAttendance
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftDeleteForm(TapirFactoryTestBase):
    def test_isValid_someAttendancesAreNotCancelled_returnsFalse(self):
        shift = ShiftFactory.create()
        for state in [
            ShiftAttendance.State.PENDING,
            ShiftAttendance.State.DONE,
            ShiftAttendance.State.CANCELLED,
        ]:
            tapir_user = TapirUserFactory.create()
            ShiftAttendance.objects.create(
                user=tapir_user,
                slot=shift.slots.first(),
                state=state,
            )

        data = {
            "confirm_understood": True,
        }
        form = ShiftDeleteForm(shift=shift, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(1, len(form.errors["__all__"]))
        self.assertIn(
            "all member attendances must be set to 'Cancelled'",
            form.errors["__all__"][0],
        )

    def test_isValid_allAttendancesCancelled_returnsTrue(self):
        shift = ShiftFactory.create()
        for state in [
            ShiftAttendance.State.CANCELLED,
            ShiftAttendance.State.CANCELLED,
            ShiftAttendance.State.CANCELLED,
        ]:
            tapir_user = TapirUserFactory.create()
            ShiftAttendance.objects.create(
                user=tapir_user,
                slot=shift.slots.first(),
                state=state,
            )

        data = {
            "confirm_understood": True,
        }
        form = ShiftDeleteForm(shift=shift, data=data)
        self.assertTrue(form.is_valid())

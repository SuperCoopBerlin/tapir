import datetime
from unittest.mock import Mock

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftSlot,
    ShiftAttendanceTemplate,
    ShiftSlotTemplate,
)
from tapir.shifts.services.self_unregister_service import SelfUnregisterService
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestSelfUnregisterService(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=3, day=4)

    def setUp(self) -> None:
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_shouldShowIsAbcdAttendanceReason_shiftIsNotAbcd_returnsFalse(self):
        tapir_user = TapirUserFactory.create()
        ShiftFactory.create()
        attendance = ShiftAttendance.objects.create(
            user=tapir_user, slot=ShiftSlot.objects.get()
        )

        self.assertFalse(
            SelfUnregisterService.should_show_is_abcd_attendance_reason(
                user=tapir_user, attendance=attendance
            )
        )

    def test_shouldShowIsAbcdAttendanceReason_shiftIsAbcdButAttendanceIsNotAbcd_returnsFalse(
        self,
    ):
        shift_template = ShiftTemplateFactory.create()
        shift_template.create_shift(datetime.date(year=2024, month=10, day=5))
        tapir_user = TapirUserFactory.create()
        attendance = ShiftAttendance.objects.create(
            user=tapir_user, slot=ShiftSlot.objects.get()
        )

        self.assertFalse(
            SelfUnregisterService.should_show_is_abcd_attendance_reason(
                user=tapir_user, attendance=attendance
            )
        )

    def test_shouldShowIsAbcdAttendanceReason_shiftIsFromAnAbcdAttendance_returnsTrue(
        self,
    ):
        shift_template = ShiftTemplateFactory.create()
        tapir_user = TapirUserFactory.create()
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=ShiftSlotTemplate.objects.get()
        )
        shift_template.create_shift(datetime.date(year=2024, month=10, day=5))

        self.assertTrue(
            SelfUnregisterService.should_show_is_abcd_attendance_reason(
                user=tapir_user, attendance=ShiftAttendance.objects.get()
            )
        )

    def test_shouldShowNotEnoughDaysBeforeShiftReason_dateIsNotEnoughDaysBeforeShift_returnsTrue(
        self,
    ):
        attendance = Mock()
        attendance.slot.shift.start_time = self.NOW + datetime.timedelta(days=6)

        self.assertTrue(
            SelfUnregisterService.should_show_not_enough_days_before_shift_reason(
                attendance=attendance
            )
        )

    def test_shouldShowNotEnoughDaysBeforeShiftReason_dateIsEnoughDaysBeforeShift_returnsFalse(
        self,
    ):
        attendance = Mock()
        attendance.slot.shift.start_time = self.NOW + datetime.timedelta(days=8)

        self.assertFalse(
            SelfUnregisterService.should_show_not_enough_days_before_shift_reason(
                attendance=attendance
            )
        )

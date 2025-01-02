import datetime

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftSlot,
    ShiftAttendanceTemplate,
    ShiftSlotTemplate,
)
from tapir.shifts.services.self_unregister_service import SelfUnregisterService
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestSelfUnregisterService(TapirFactoryTestBase):
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

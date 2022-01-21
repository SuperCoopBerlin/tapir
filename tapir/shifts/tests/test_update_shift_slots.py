import datetime
from datetime import time

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftSlotTemplate,
    ShiftUserCapability,
    ShiftSlot,
    ShiftAttendanceTemplate,
    ShiftAttendance,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestUpdateShiftSlots(TapirSeleniumTestBase):
    SLOT_NAME_CASHIER = "Kasse"
    SLOT_NAME_STORAGE = "Warenannahme & Lagerhaltung"
    SLOT_NAME_LEADER = "Teamleitung"
    SLOT_NAME_GENERAL = ""

    def test_update_shift_slots(self):
        shift_template = ShiftTemplate.objects.create(
            weekday=0,
            start_time=time(hour=8, minute=0),
            end_time=time(hour=9, minute=0),
        )

        ShiftSlotTemplate.objects.create(
            name=self.SLOT_NAME_CASHIER,
            shift_template=shift_template,
            required_capabilities=[ShiftUserCapability.CASHIER],
        )
        general_slot_template = ShiftSlotTemplate.objects.create(
            name=self.SLOT_NAME_GENERAL, shift_template=shift_template
        )
        ShiftAttendanceTemplate.objects.create(
            slot_template=general_slot_template,
            user=TapirUser.objects.get(
                username=self.get_vorstand_user().get_username()
            ),
        )
        for index in range(2):
            slot_template = ShiftSlotTemplate.objects.create(
                name=self.SLOT_NAME_STORAGE,
                shift_template=shift_template,
            )
            if index == 0:
                ShiftAttendanceTemplate.objects.create(
                    slot_template=slot_template,
                    user=TapirUser.objects.get(
                        username=self.get_standard_user().get_username()
                    ),
                )
        for index in range(2):
            slot_template = ShiftSlotTemplate.objects.create(
                name=self.SLOT_NAME_LEADER,
                shift_template=shift_template,
            )
            if index == 1:
                ShiftAttendanceTemplate.objects.create(
                    slot_template=slot_template,
                    user=TapirUser.objects.get(
                        username=self.get_member_office_user().get_username()
                    ),
                )

        past_shift = shift_template.create_shift(
            start_date=datetime.date(day=10, month=1, year=2022)
        )
        future_shift = shift_template.create_shift(
            start_date=datetime.date(day=17, month=1, year=2022)
        )

        alan_duval_slot = ShiftSlot.objects.get(
            shift=future_shift,
            name=self.SLOT_NAME_STORAGE,
            attendances__user__first_name=None,
        )
        ShiftAttendance.objects.create(
            slot=alan_duval_slot,
            user=TapirUser.objects.get(username="alan.duval"),
        )

        desired_slots = {
            self.SLOT_NAME_CASHIER: 2,
            self.SLOT_NAME_STORAGE: 1,
            self.SLOT_NAME_GENERAL: 0,
            self.SLOT_NAME_LEADER: 1,
        }
        deletion_warnings = shift_template.update_slots(
            desired_slots,
            timezone.make_aware(
                datetime.datetime(day=15, month=1, year=2022, hour=12, minute=0)
            ),
        )

        self.assertEqual(
            2,
            future_shift.slots.filter(name=self.SLOT_NAME_CASHIER).count(),
            "The update function should have created a second cashier slot",
        )
        self.assertEqual(
            1,
            past_shift.slots.filter(name=self.SLOT_NAME_CASHIER).count(),
            "The update function should only create slots in the future",
        )
        self.assertEqual(
            0,
            future_shift.slots.filter(name=self.SLOT_NAME_GENERAL).count(),
            "The future shift should have no general slot",
        )
        self.assertTrue(
            ShiftSlotTemplate.objects.get(
                shift_template=shift_template, name=self.SLOT_NAME_STORAGE
            ).get_attendance_template()
            is not None
        )
        self.assertTrue(
            ShiftSlotTemplate.objects.get(
                shift_template=shift_template, name=self.SLOT_NAME_LEADER
            ).get_attendance_template()
            is not None
        )

        for slot in ShiftSlot.objects.filter(
            shift=future_shift, name=self.SLOT_NAME_CASHIER
        ):
            self.assertEqual(
                slot.required_capabilities,
                [ShiftUserCapability.CASHIER],
                "The second created cashier slot should have copied the required_capability from the original slot",
            )

        found_warning_abcd = False
        found_warning_not_abcd = False
        for warning in deletion_warnings:
            if (
                warning["user"]
                == TapirUser.objects.get(
                    username=self.get_vorstand_user().get_username()
                )
                and warning["slot_name"] == general_slot_template.get_display_name()
                and warning["is_ABCD"]
            ):
                found_warning_abcd = True

            if (
                warning["user"] == TapirUser.objects.get(username="alan.duval")
                and warning["slot_name"] == alan_duval_slot.get_display_name()
                and not warning["is_ABCD"]
            ):
                found_warning_not_abcd = True

        self.assertTrue(
            found_warning_abcd,
            "There should be a warning about a user loosing their ABCD slot",
        )
        self.assertTrue(
            found_warning_not_abcd,
            "There should be a warning about a user loosing their not ABCD slot",
        )
        self.assertEqual(
            2,
            len(deletion_warnings),
            "2 users should have lost their slots, so their should be 2 warnings",
        )

from django.conf import settings
from django.urls import reverse

from tapir.shifts.models import ShiftAttendance
from tapir.shifts.tests.factories import ShiftSlotFactory, ShiftFactory
from tapir.utils.tests_utils import PermissionTestMixin, TapirFactoryTestBase


class TestDeleteShiftSlotView(PermissionTestMixin, TapirFactoryTestBase):
    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
        ]

    def do_request(self):
        shift = ShiftFactory.create()
        slot = ShiftSlotFactory.create(shift=shift)
        return self.client.get(reverse("shifts:shift_slot_delete", args=[slot.id]))

    def test_deleteShiftSlotView_validAttendanceExists_returnsError(self):
        shift = ShiftFactory.create()
        slot = ShiftSlotFactory.create(shift=shift)
        user = self.login_as_vorstand()
        ShiftAttendance.objects.create(
            user=user, slot=slot, state=ShiftAttendance.State.DONE
        )

        response = self.client.post(
            reverse("shifts:shift_slot_delete", args=[slot.id]),
            data={"confirm_understood": True},
        )

        slot.refresh_from_db()
        self.assertFalse(slot.deleted)

        self.assertStatusCode(response, 200)
        self.assertEqual(1, len(response.context["form"].errors))
        self.assertEqual(1, len(response.context["form"].errors["__all__"]))

    def test_deleteShiftSlotView_cancelledValidAttendanceExists_slotMarkedAsDeleted(
        self,
    ):
        shift = ShiftFactory.create()
        slot = ShiftSlotFactory.create(shift=shift)
        user = self.login_as_vorstand()
        ShiftAttendance.objects.create(
            user=user, slot=slot, state=ShiftAttendance.State.CANCELLED
        )

        response = self.client.post(
            reverse("shifts:shift_slot_delete", args=[slot.id]),
            data={"confirm_understood": True},
        )

        slot.refresh_from_db()
        self.assertTrue(slot.deleted)
        self.assertRedirects(response, shift.get_absolute_url())

    def test_deleteShiftSlotView_noAttendanceExists_slotMarkedAsDeleted(self):
        shift = ShiftFactory.create()
        slot = ShiftSlotFactory.create(shift=shift)
        self.login_as_vorstand()
        self.assertFalse(ShiftAttendance.objects.exists())

        response = self.client.post(
            reverse("shifts:shift_slot_delete", args=[slot.id]),
            data={"confirm_understood": True},
        )

        slot.refresh_from_db()
        self.assertTrue(slot.deleted)
        self.assertRedirects(response, shift.get_absolute_url())

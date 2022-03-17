import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendance,
    ShiftSlotWarning,
    ShiftUserCapability,
)
from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.tests.utils import register_user_to_shift
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMemberSelfRegisters(TapirFactoryTestBase):
    def test_member_self_registers(self):
        user = self.login_as_normal_user()
        shift = self.create_shift_in_the_future()

        response = register_user_to_shift(self.client, user, shift)
        self.check_registration_successful(response, user, shift)

    def test_member_self_registers_with_warning(self):
        shift = self.create_shift_in_the_future()
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        warning = ShiftSlotWarning.MUST_BE_ABLE_TO_CARRY_HEAVY_WEIGHTS
        slot.warnings = [warning]
        slot.save()

        user = self.login_as_normal_user()
        response = self.client.get(reverse("shifts:slot_register", args=[slot.id]))
        self.assertIn(
            f"warning_{warning}",
            response.content.decode(),
            "The register page should display the warning.",
        )

        self.client.post(
            reverse("shifts:slot_register", args=[slot.id]),
            {"user": user.id, f"warning_{warning}": False},
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift).count(),
            0,
            "The attendance should not have been created.",
        )

        response = self.client.post(
            reverse("shifts:slot_register", args=[slot.id]),
            {"user": user.id, f"warning_{warning}": True},
        )
        self.check_registration_successful(response, user, shift)

    def test_member_self_registers_with_capability(self):
        shift = self.create_shift_in_the_future()
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        capability = ShiftUserCapability.SHIFT_COORDINATOR
        slot.required_capabilities = [capability]
        slot.save()

        user = self.login_as_normal_user()
        user.shift_user_data.capabilities = [capability]
        user.shift_user_data.save()

        response = register_user_to_shift(self.client, user, shift)
        self.check_registration_successful(response, user, shift)

    def test_member_self_registers_without_capability(self):
        shift = self.create_shift_in_the_future()
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        capability = ShiftUserCapability.SHIFT_COORDINATOR
        slot.required_capabilities = [capability]
        slot.save()

        user = self.login_as_normal_user()
        user.shift_user_data.capabilities = []
        user.shift_user_data.save()

        response = register_user_to_shift(self.client, user, shift)
        self.assertEqual(
            response.status_code,
            403,
            "Normal users should not be able to register themselves to a slot that they don't have the capability for.",
        )

    def test_member_self_registers_in_the_past(self):
        user = self.login_as_normal_user()
        start_time = timezone.now() - datetime.timedelta(hours=0, minutes=30)
        shift = ShiftFactory.create(start_time=start_time)
        self.assertFalse(shift.is_in_the_future(), "The shift should be in the past.")

        response = register_user_to_shift(self.client, user, shift)
        self.assertEqual(
            response.status_code,
            403,
            "Normal users should not be able to register themselves to a shifts that are in the past.",
        )

    def create_shift_in_the_future(self):
        start_time = timezone.now() + datetime.timedelta(hours=0, minutes=30)
        shift = ShiftFactory.create(start_time=start_time)
        self.assertTrue(shift.is_in_the_future(), "The shift should be in the future.")
        return shift

    def check_registration_successful(self, response, user, shift):
        self.assertRedirects(
            response,
            shift.get_absolute_url(),
            msg_prefix="The registration should be successful and therefore redirect to the shift's page.",
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift).count(),
            1,
            "Exactly one attendance should have been created.",
        )

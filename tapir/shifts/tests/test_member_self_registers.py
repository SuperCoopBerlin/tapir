import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendance,
    ShiftAttendanceTemplate,
)
from tapir.shifts.tests.factories import (
    ShiftFactory,
    ShiftTemplateFactory,
    ShiftUserCapabilityFactory,
    ShiftSlotWarningFactory,
)
from tapir.shifts.tests.utils import (
    register_user_to_shift,
    check_registration_successful,
    register_user_to_shift_template,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMemberSelfRegisters(TapirFactoryTestBase):
    def test_member_self_registers(self):
        user = self.login_as_normal_user()
        shift = self.create_shift_in_the_future()

        response = register_user_to_shift(self.client, user, shift)
        check_registration_successful(self, response, user, shift)

    def test_member_self_registers_with_warning(self):
        shift = self.create_shift_in_the_future()
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        warning = ShiftSlotWarningFactory.create()
        slot.warnings.set([warning])

        user = self.login_as_normal_user(share_owner__is_investing=False)
        response = self.client.get(reverse("shifts:slot_register", args=[slot.id]))
        self.assertIn(
            f"warning_{warning.id}",
            response.content.decode(),
            "The register page should display the warning.",
        )

        self.client.post(
            reverse("shifts:slot_register", args=[slot.id]),
            {"user": user.id, f"warning_{warning.id}": False},
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift).count(),
            0,
            "The attendance should not have been created.",
        )

        response = self.client.post(
            reverse("shifts:slot_register", args=[slot.id]),
            {"user": user.id, f"warning_{warning.id}": True},
        )
        check_registration_successful(self, response, user, shift)

    def test_member_self_registers_with_capability(self):
        shift = self.create_shift_in_the_future()
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        capability = ShiftUserCapabilityFactory.create()
        slot.required_capabilities.set([capability])

        user = self.login_as_normal_user(share_owner__is_investing=False)
        user.shift_user_data.capabilities.set([capability])

        response = register_user_to_shift(self.client, user, shift)
        check_registration_successful(self, response, user, shift)

    def test_member_self_registers_without_capability(self):
        shift = self.create_shift_in_the_future()
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        capability = ShiftUserCapabilityFactory.create()
        slot.required_capabilities.set([capability])

        user = self.login_as_normal_user()
        user.shift_user_data.capabilities.set([])

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

    def test_member_self_registers_to_abcd_shift(self):
        user = self.login_as_normal_user()
        shift_template = ShiftTemplateFactory.create()

        response = register_user_to_shift_template(self.client, user, shift_template)
        self.assertEqual(
            response.status_code,
            403,
            "Non-member-office users should not be be able to register themselves to ABCD shifts.",
        )
        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(user=user).exists(),
            "The shift attendance template should not have been created.",
        )

    def test_member_cant_register_to_cancelled_shift(self):
        user = self.login_as_normal_user()
        shift = self.create_shift_in_the_future()
        shift.cancelled = True
        shift.save()

        response = register_user_to_shift(self.client, user, shift)
        self.assertEqual(
            response.status_code,
            403,
            "Normal members should not be able to register themselves to cancelled shift.",
        )

    def create_shift_in_the_future(self):
        start_time = timezone.now() + datetime.timedelta(hours=0, minutes=30)
        shift = ShiftFactory.create(start_time=start_time)
        self.assertTrue(shift.is_in_the_future(), "The shift should be in the future.")
        return shift

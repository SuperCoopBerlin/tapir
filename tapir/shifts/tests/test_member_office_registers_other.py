import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendance,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
    ShiftExemption,
    ShiftTemplate,
)
from tapir.shifts.tests.factories import (
    ShiftFactory,
    ShiftTemplateFactory,
    ShiftUserCapabilityFactory,
)
from tapir.shifts.tests.utils import (
    register_user_to_shift,
    check_registration_successful,
    register_user_to_shift_template,
    check_registration_successful_template,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMemberRegistersOther(TapirFactoryTestBase):
    def test_member_registers_other_flying(self):
        user = TapirUserFactory.create()
        shift = ShiftFactory.create()

        self.login_as_member_office_user()
        response = register_user_to_shift(self.client, user, shift)
        check_registration_successful(self, response, user, shift)

    def test_member_registers_other_flying_warning_no_capability(self):
        user = TapirUserFactory.create()
        shift = ShiftFactory.create()
        slot = ShiftSlot.objects.filter(shift=shift).first()
        slot.required_capabilities.set([ShiftUserCapabilityFactory.create()])
        slot.save()

        self.login_as_member_office_user()
        response = self.client.post(
            reverse("shifts:slot_register", args=[slot.id]), {"user": user.id}
        )
        self.assertIn(
            "confirm_missing_capabilities",
            response.content.decode(),
            "There should be a warning about missing capabilities.",
        )
        self.assertFalse(
            ShiftAttendance.objects.filter(user=user).exists(),
            "The shift attendance should not have been created.",
        )

        response = self.client.post(
            reverse("shifts:slot_register", args=[slot.id]),
            {"user": user.id, "confirm_missing_capabilities": True},
        )
        check_registration_successful(self, response, user, shift)

    def test_member_registers_other_abcd(self):
        user = TapirUserFactory.create()
        shift_template = ShiftTemplateFactory.create()
        shift_1 = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )

        self.login_as_member_office_user()
        response = register_user_to_shift_template(self.client, user, shift_template)

        check_registration_successful_template(self, response, user, shift_template)

        shift_2 = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=2)
        )

        self.assertEqual(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift_1).count(),
            1,
            "There should be exactly one attendance for the shift that was created before registration.",
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift_2).count(),
            1,
            "There should be exactly one attendance for the shift that was created after registration.",
        )

    def test_member_registers_other_abcd_warning_missing_capability(self):
        user = TapirUserFactory.create()
        shift_template = ShiftTemplateFactory.create()
        slot_template = ShiftSlotTemplate.objects.filter(
            shift_template=shift_template
        ).get()
        slot_template.required_capabilities.set([ShiftUserCapabilityFactory.create()])
        slot_template.save()

        self.login_as_member_office_user()
        response = register_user_to_shift_template(self.client, user, shift_template)
        response_content = response.content.decode()

        self.assertIn(
            "confirm_missing_capabilities",
            response_content,
            "There should be a warning about missing capabilities.",
        )
        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(user=user).exists(),
            "The shift attendance should not have been created.",
        )

        response = self.client.post(
            reverse("shifts:slottemplate_register", args=[slot_template.id]),
            {"user": user.id, "confirm_missing_capabilities": True},
        )
        check_registration_successful_template(self, response, user, shift_template)

    def test_member_registers_other_warning_occupied(self):
        abcd_user = TapirUserFactory.create()
        flying_user = TapirUserFactory.create()
        shift_template = ShiftTemplateFactory.create()

        shift_free = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        shift_occupied = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=8)
        )

        ShiftAttendance.objects.create(
            user=flying_user,
            slot=ShiftSlot.objects.filter(shift=shift_occupied).first(),
        )

        self.login_as_member_office_user()
        slot_template = ShiftSlotTemplate.objects.filter(
            shift_template=shift_template
        ).first()
        response = self.client.get(
            reverse("shifts:slottemplate_register", args=[slot_template.id])
        )
        response_content = response.content.decode()

        self.assertIn(
            "occupied_shifts_list",
            response_content,
            "There should be a warning about occupied shifts.",
        )
        self.assertIn(
            shift_occupied.get_display_name(),
            response_content,
            "The name of the occupied shifts should be in the warning list.",
        )

        register_user_to_shift_template(self.client, abcd_user, shift_template)
        self.assertEqual(
            ShiftAttendance.objects.get(slot__shift=shift_free).user,
            abcd_user,
            "The ABCD user should be registered to the shift that was free.",
        )
        self.assertEqual(
            ShiftAttendance.objects.get(slot__shift=shift_occupied).user,
            flying_user,
            "The flying user should be have kept their shift.",
        )

    def test_member_registers_after_unregister(self):
        user = TapirUserFactory.create()
        shift_template = ShiftTemplateFactory.create()
        shift = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )

        self.login_as_member_office_user()
        register_user_to_shift_template(self.client, user, shift_template)

        attendance_template = ShiftAttendanceTemplate.objects.get(user=user)
        self.client.post(
            reverse(
                "shifts:shift_attendance_template_delete", args=[attendance_template.id]
            )
        )

        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(user=user).exists(),
            "The user should be unregistered from the ABCD shift.",
        )
        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift).state,
            ShiftAttendance.State.CANCELLED,
            "After being unregistered from the ABCD shift, the attendance for the normal shift should be cancelled.",
        )

        response = register_user_to_shift_template(self.client, user, shift_template)
        check_registration_successful_template(self, response, user, shift_template)
        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift).state,
            ShiftAttendance.State.PENDING,
            "After being re-registered to the ABCD shift, the user should also get his normal attendances back.",
        )

    def test_register_user_to_abcd_during_exemption(self):
        user: TapirUser = TapirUserFactory.create()
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_1 = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=10)
        )
        shift_2 = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=30)
        )
        shift_3 = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=50)
        )

        ShiftExemption.objects.create(
            shift_user_data=user.shift_user_data,
            start_date=timezone.now().date() + datetime.timedelta(days=20),
            end_date=timezone.now().date() + datetime.timedelta(days=40),
        )
        self.login_as_member_office_user()
        register_user_to_shift_template(self.client, user, shift_template)

        self.assertTrue(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift_1).exists(),
            "There first shift is before the exemption, it should have an attendance.",
        )
        self.assertFalse(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift_2).exists(),
            "There second shift is during the exemption, it should not have an attendance.",
        )
        self.assertTrue(
            ShiftAttendance.objects.filter(user=user, slot__shift=shift_3).exists(),
            "There third shift is after the exemption, it should have an attendance.",
        )

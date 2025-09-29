import datetime

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import ShiftAttendanceTemplate, ShiftAttendance, ShiftSlot
from tapir.shifts.tests.factories import (
    ShiftTemplateFactory,
)
from tapir.utils.tests_utils import PermissionTestMixin, TapirFactoryTestBase


class TestDeleteShiftSlotTemplateView(PermissionTestMixin, TapirFactoryTestBase):
    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
        ]

    def do_request(self):
        shift_template = ShiftTemplateFactory.create()
        return self.client.get(
            reverse(
                "shifts:shift_slot_template_delete",
                args=[shift_template.slot_templates.first().id],
            )
        )

    def test_deleteShiftSlotTemplateView_attendanceTemplateExists_returnsError(self):
        shift_template = ShiftTemplateFactory.create()
        user = self.login_as_vorstand()
        slot_template = shift_template.slot_templates.first()
        ShiftAttendanceTemplate.objects.create(user=user, slot_template=slot_template)

        response = self.client.post(
            reverse("shifts:shift_slot_template_delete", args=[slot_template.id]),
            data={"confirm_understood": True},
        )

        self.assertStatusCode(response, 200)
        slot_template.refresh_from_db()
        self.assertFalse(slot_template.deleted)

        self.assertEqual(1, len(response.context["form"].errors))
        self.assertEqual(1, len(response.context["form"].errors["__all__"]))

    def test_deleteShiftSlotTemplateView_futureAttendanceExists_returnsError(self):
        shift_template = ShiftTemplateFactory.create()
        user = self.login_as_vorstand()
        slot_template = shift_template.slot_templates.first()
        shift = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        ShiftAttendance.objects.create(
            user=user, slot=shift.slots.first(), state=ShiftAttendance.State.PENDING
        )

        response = self.client.post(
            reverse("shifts:shift_slot_template_delete", args=[slot_template.id]),
            data={"confirm_understood": True},
        )

        self.assertStatusCode(response, 200)
        slot_template.refresh_from_db()
        self.assertFalse(slot_template.deleted)

        self.assertEqual(1, len(response.context["form"].errors))
        self.assertEqual(1, len(response.context["form"].errors["__all__"]))

    def test_deleteShiftSlotTemplateView_pastAttendanceTemplateExists_markSlotTemplateAsDeleted(
        self,
    ):
        shift_template = ShiftTemplateFactory.create()
        user = self.login_as_vorstand()
        slot_template = shift_template.slot_templates.first()
        shift = shift_template.create_shift(
            start_date=timezone.now().date() - datetime.timedelta(days=7)
        )
        ShiftAttendance.objects.create(
            user=user, slot=shift.slots.first(), state=ShiftAttendance.State.PENDING
        )

        response = self.client.post(
            reverse("shifts:shift_slot_template_delete", args=[slot_template.id]),
            data={"confirm_understood": True},
        )

        self.assertRedirects(response, shift_template.get_absolute_url())
        slot_template.refresh_from_db()
        self.assertTrue(slot_template.deleted)
        self.assertFalse(ShiftSlot.objects.get().deleted)

    def test_deleteShiftSlotTemplateView_noAttendance_markSlotTemplateAsDeleted(self):
        shift_template = ShiftTemplateFactory.create()
        self.login_as_vorstand()
        slot_template = shift_template.slot_templates.first()
        shift_template.create_shift(
            start_date=timezone.now().date() - datetime.timedelta(days=1)
        )

        response = self.client.post(
            reverse("shifts:shift_slot_template_delete", args=[slot_template.id]),
            data={"confirm_understood": True},
        )

        self.assertRedirects(response, shift_template.get_absolute_url())
        slot_template.refresh_from_db()
        self.assertTrue(slot_template.deleted)
        self.assertTrue(ShiftSlot.objects.get().deleted)

    def test_deleteShiftSlotTemplateView_notConfirmed_returnsError(self):
        shift_template = ShiftTemplateFactory.create()
        self.login_as_vorstand()
        slot_template = shift_template.slot_templates.first()
        shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )

        response = self.client.post(
            reverse("shifts:shift_slot_template_delete", args=[slot_template.id]),
            data={"confirm_understood": False},
        )

        self.assertStatusCode(response, 200)
        slot_template.refresh_from_db()
        self.assertFalse(slot_template.deleted)

        self.assertEqual(1, len(response.context["form"].errors))
        self.assertEqual(1, len(response.context["form"].errors["confirm_understood"]))

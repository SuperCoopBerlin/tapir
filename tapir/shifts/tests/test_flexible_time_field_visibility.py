import datetime

from django.forms import HiddenInput
from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.shifts.models import ShiftTemplate
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_is_working,
)


class TestFlexibleTime(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=6, day=15)

    def setUp(self) -> None:
        self.NOW = mock_timezone_now(self, self.NOW)

    def assertTimeFieldShown(self, response):
        field = response.context_data["form"].fields["custom_time"]
        self.assertTrue(field.required)
        self.assertFalse(isinstance(field.widget, HiddenInput))

    def assertTimeFieldHidden(self, response):
        field = response.context_data["form"].fields["custom_time"]
        self.assertFalse(field.required)
        self.assertTrue(isinstance(field.widget, HiddenInput))

    def test_registerUserToShiftSlotForm_shiftDoesntHaveFlexibleTime_timeFieldHidden(
        self,
    ):
        tapir_user = create_member_that_is_working(self, self.NOW)
        self.login_as_user(tapir_user)
        shift = ShiftFactory.create(
            flexible_time=False, start_time=self.NOW + datetime.timedelta(days=10)
        )

        response: TemplateResponse = self.client.get(
            reverse("shifts:slot_register", args=[shift.slots.first().id])
        )

        self.assertTimeFieldHidden(response)

    def test_registerUserToShiftSlotForm_shiftHasFlexibleTime_timeFieldShown(self):
        self.login_as_normal_user(share_owner__is_investing=False)

        shift = ShiftFactory.create(
            flexible_time=True, start_time=self.NOW + datetime.timedelta(days=10)
        )

        response: TemplateResponse = self.client.get(
            reverse("shifts:slot_register", args=[shift.slots.first().id])
        )

        self.assertTimeFieldShown(response)

    def test_shiftTemplateCreateShift_templateHasFlexibleTimeEnabled_createdShiftAlsoHasFlexibleTimeEnabled(
        self,
    ):
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(flexible_time=True)
        shift = shift_template.create_shift_if_necessary(
            datetime.date(year=2024, month=6, day=15)
        )
        self.assertTrue(shift_template.flexible_time)
        self.assertTrue(shift.flexible_time)

    def test_shiftAttendanceTemplateForm_shiftTemplateDoesntHaveFlexibleTime_timeFieldHidden(
        self,
    ):
        self.login_as_member_office_user()
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(flexible_time=False)

        response: TemplateResponse = self.client.get(
            reverse(
                "shifts:slottemplate_register",
                args=[shift_template.slot_templates.first().id],
            )
        )

        self.assertTimeFieldHidden(response)

    def test_shiftAttendanceTemplateForm_shiftTemplateHasFlexibleTime_timeFieldShown(
        self,
    ):
        self.login_as_member_office_user()
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(flexible_time=True)

        response: TemplateResponse = self.client.get(
            reverse(
                "shifts:slottemplate_register",
                args=[shift_template.slot_templates.first().id],
            )
        )

        self.assertTimeFieldShown(response)

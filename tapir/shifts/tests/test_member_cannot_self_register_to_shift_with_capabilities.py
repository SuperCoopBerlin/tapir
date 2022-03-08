import datetime

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import Shift, ShiftSlot, ShiftUserCapability
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestMemberCannotSelfRegisterToShiftWithCapabilities(TapirSeleniumTestBase):
    @tag("selenium")
    def test_member_cannot_self_register_to_shift_with_capabilities(self):
        shift = Shift.objects.create(
            start_time=timezone.now().date() + datetime.timedelta(days=1),
            end_time=timezone.now().date() + datetime.timedelta(days=1, hours=3),
        )
        slot = ShiftSlot.objects.create(
            shift=shift, required_capabilities=[ShiftUserCapability.SHIFT_COORDINATOR]
        )

        standard_user = self.get_standard_user()
        self.login(standard_user.get_username(), standard_user.get_username())
        self.selenium.get(
            self.live_server_url + reverse("shifts:shift_detail", args=[shift.pk])
        )
        self.wait_until_element_present_by_id("shift_detail_card")
        button = self.selenium.find_element_by_class_name("register-to-slot-button")
        self.assertTrue(
            self.is_button_disabled(button),
            "The register self button should be disabled because the user doesn't have the required capability.",
        )

        self.selenium.get(
            self.live_server_url + reverse("shifts:slot_register", args=[slot.pk])
        )
        self.assertIn(
            "403 Forbidden",
            self.selenium.find_element_by_tag_name("h1").text,
            "If the user manipulates the HTML to click the disabled button anyway, it should result in an error",
        )

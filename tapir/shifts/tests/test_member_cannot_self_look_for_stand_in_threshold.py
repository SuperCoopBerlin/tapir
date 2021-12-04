from datetime import timedelta

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import (
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestMemberCannotSelfLookForStandInThreshold(TapirSeleniumTestBase):
    @tag("selenium")
    def test_member_cannot_self_look_for_stand_in_threshold(self):
        standard_user = self.get_standard_user()
        self.login(standard_user.get_username(), standard_user.get_username())

        start_time = timezone.now() + timedelta(
            days=Shift.NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN - 1
        )
        end_time = start_time + timedelta(hours=3)
        shift = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot = ShiftSlot.objects.create(shift=shift)
        self.selenium.get(
            self.live_server_url + reverse("shifts:shift_detail", args=[shift.pk])
        )
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_element_by_class_name("register-self-button").click()
        self.wait_until_element_present_by_id("self_look_for_stand_in_button")
        self.assertFalse(
            slot.user_can_look_for_standin(standard_user.get_tapir_user()),
            "The user should not be able to look for a stand-in because the shift is too close to now.",
        )
        self.assertTrue(
            self.is_button_disabled(
                self.selenium.find_element_by_id("self_look_for_stand_in_button")
            ),
            "The look for stand-in button should be disabled because the shift is too close to now.",
        )

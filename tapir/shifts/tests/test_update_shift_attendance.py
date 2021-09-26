from datetime import timedelta

from django.test import tag
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftAttendance,
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase, TAPIR_SELENIUM_BASE_FIXTURES


class TestUpdateShiftAttendance(TapirSeleniumTestBase):
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES + ["test_update_shift_attendance.json"]

    @tag("selenium")
    def test_update_shift_attendance(self):
        hilla = TapirUser.objects.get(username="hilla.waisanen")
        member_office_user = self.get_member_office_user().get_tapir_user()
        self.login(member_office_user.username, member_office_user.username)

        self.assertEqual(
            0,
            hilla.shift_user_data.get_account_balance(),
            "The test assumes that the standard_user starts with a shift credit of 0",
        )

        self.selenium.get(self.live_server_url + hilla.get_absolute_url())
        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.assertIn(
            "Up to date",
            self.selenium.find_element_by_id("user-shift-status").text,
            "User's shift status should be up to date because we just checked that it's shift credit score is 0.",
        )

        for _ in range(2):
            self.create_shift_and_update_attendance(hilla, "button-mark-attended")

        self.assertEqual(
            2,
            hilla.shift_user_data.get_account_balance(),
            "We just marked 2 shifts as attended so we should have a shift score of 2",
        )

        self.selenium.get(self.live_server_url + hilla.get_absolute_url())
        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.assertIn(
            "2 banked shifts",
            self.selenium.find_element_by_id("user-shift-status").text,
            "User's shift detail page should show 2 banked shifts.",
        )

        for _ in range(4):
            self.create_shift_and_update_attendance(hilla, "button-mark-missed")

        self.assertEqual(
            -2,
            hilla.shift_user_data.get_account_balance(),
            "The user attended 2 shifts and missed 4 so they should have a score of -2",
        )

        self.selenium.get(self.live_server_url + hilla.get_absolute_url())
        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.assertIn(
            "On alert (-2)",
            self.selenium.find_element_by_id("user-shift-status").text,
            "User's shift detail page should show the alert status and the correct shift score.",
        )

    def create_shift_and_update_attendance(self, user: TapirUser, button_class: str):
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=3)
        shift = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot = ShiftSlot.objects.create(shift=shift)
        ShiftAttendance.objects.create(slot=slot, user=user)
        self.selenium.get(self.live_server_url + shift.get_absolute_url())
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_element_by_class_name(button_class).click()

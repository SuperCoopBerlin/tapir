from datetime import timedelta

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftAttendance,
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase, TAPIR_SELENIUM_BASE_FIXTURES


class TestShiftAttendanceExcused(TapirSeleniumTestBase):
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES + ["test_update_shift_attendance.json"]
    description = "A_TEST_DESCRIPTION"

    @tag("selenium")
    def test_shift_attendance_excused(self):
        hilla: TapirUser = TapirUser.objects.get(username="hilla.waisanen")
        member_office_user = self.get_member_office_user().get_tapir_user()
        self.login(member_office_user.username, member_office_user.username)

        self.assertEqual(
            0,
            hilla.shift_user_data.get_account_balance(),
            "The test assumes that the standard_user starts with a shift credit of 0",
        )

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=3)
        shift = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot = ShiftSlot.objects.create(shift=shift)
        ShiftAttendance.objects.create(slot=slot, user=hilla)
        self.selenium.get(self.live_server_url + shift.get_absolute_url())
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_element_by_class_name("member-office-excused-button").click()
        self.wait_until_element_present_by_id("shift_attendance_form")

        self.selenium.find_element_by_id("id_description").send_keys(self.description)
        self.selenium.find_element_by_id("save_button").click()
        self.wait_until_element_present_by_id("shift_detail_card")

        self.assertEqual(
            1,
            hilla.shift_user_data.get_account_balance(),
            "We just marked 1 shifts as excused so we should have a shift score of 1",
        )

        self.selenium.get(
            self.live_server_url
            + reverse("shifts:user_shift_account_log", args=[hilla.id])
        )
        self.wait_until_element_present_by_id("user_shift_account_log")
        self.assertIn(
            self.description,
            self.selenium.find_element_by_class_name("description").text,
            "The description that we put in the form should show on the log",
        )

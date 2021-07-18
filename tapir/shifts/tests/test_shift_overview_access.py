from django.test import tag
from django.urls import reverse

from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestShiftOverviewAccess(TapirSeleniumTestBase):
    @tag("selenium")
    def test_access_shift_overviews(self):
        user = self.get_standard_user()
        self.login(user.get_username(), user.get_username())

        self.selenium.get(
            self.live_server_url + reverse("shifts:shift_template_overview")
        )
        self.wait_until_element_present_by_id("repeated-shift-overview-table")

        self.selenium.get(self.live_server_url + reverse("shifts:upcoming_timetable"))
        self.wait_until_element_present_by_id("upcoming-shifts-timetable")

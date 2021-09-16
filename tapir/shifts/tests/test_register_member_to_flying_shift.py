import datetime

import django.utils.timezone
from django.test import tag
from django.urls import reverse
from selenium.webdriver.common.keys import Keys

from tapir.shifts.models import ShiftTemplate
from tapir.utils.tests_utils import TapirSeleniumTestBase, TAPIR_SELENIUM_BASE_FIXTURES


class TestRegisterAbcdMemberToAbcdShift(TapirSeleniumTestBase):
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES + [
        "test_member_self_registers_to_shift.json",
    ]
    TEMPLATE_SHIFT_ID = 1000
    SHIFT_NAME = "SeleniumTestAbcdShift"

    # register a member to an ABCD shift and check that they get registered to the corresponding shift instance
    @tag("selenium")
    def test_register_member_to_flying_shift(self):
        shift = ShiftTemplate.objects.get(id=self.TEMPLATE_SHIFT_ID).create_shift(
            django.utils.timezone.now().date() + datetime.timedelta(days=1)
        )

        other_user = self.get_test_user("hilla.waisanen")
        member_office_user = self.get_member_office_user()
        self.login(member_office_user.get_username(), member_office_user.get_username())

        self.selenium.get(self.live_server_url + reverse("shifts:upcoming_timetable"))
        self.wait_until_element_present_by_id("upcoming-shifts-timetable")
        self.selenium.find_element_by_id(f"shift_{shift.id}").click()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_elements_by_class_name("register-button")[0].click()
        self.wait_until_element_present_by_id("shift_form_card")
        self.selenium.find_element_by_id("select2-id_user-container").click()
        search_field = self.selenium.find_element_by_class_name("select2-search__field")
        search_field.send_keys(other_user.get_display_name())
        search_field.send_keys(Keys.ENTER)
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.assertEqual(
            other_user.get_display_name(),
            self.selenium.find_element_by_class_name("shift-user").text,
        )

import datetime
import time

import django.utils.timezone
from django.test import tag

from tapir.shifts.models import ShiftTemplate
from tapir.utils.tests_utils import TapirSeleniumTestBase, TAPIR_SELENIUM_BASE_FIXTURES


class TestRegisterAbcdMemberToAbcdShift(TapirSeleniumTestBase):
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES + [
        "test_register_abcd_member_to_abcd_shift.json",
    ]
    TEMPLATE_SHIFT_ID = 1000

    # register a member to an ABCD shift and check that they get registered to the corresponding shift instance
    @tag("selenium")
    def test_register_abcd_member_to_abcd_shift(self):
        ShiftTemplate.objects.get(id=self.TEMPLATE_SHIFT_ID).create_shift(
            django.utils.timezone.now().date() + datetime.timedelta(days=1)
        )

        member_office_user = self.get_member_office_user()
        self.login(member_office_user.get_username(), member_office_user.get_username())
        abcd_user = self.get_test_user("hilla.waisanen")
        self.go_to_user_page(abcd_user.get_display_name())

        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.selenium.find_element_by_id("find_abcd_shift_button").click()
        self.wait_until_element_present_by_id("repeated-shift-overview-table")
        self.selenium.find_element_by_id(f"template_{self.TEMPLATE_SHIFT_ID}").click()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_elements_by_class_name("abcd_shift_register_button")[
            0
        ].click()
        self.wait_until_element_present_by_id("shift_form_card")
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

        self.go_to_user_page(abcd_user.get_display_name())
        self.assertIn(
            "SeleniumTestAbcdShift",
            self.selenium.find_element_by_class_name("repeated-shift").text,
        )
        self.assertIn(
            "SeleniumTestAbcdShift",
            self.selenium.find_element_by_id("upcoming_shift").text,
        )

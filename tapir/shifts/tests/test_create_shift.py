import datetime
import time

from django.urls import reverse

from tapir.utils.tests_utils import TapirSeleniumTestBase
from django.test import tag


class TestCreateShift(TapirSeleniumTestBase):
    shift_name = "THE_TEST_SHIFT"
    shift_start_time = datetime.datetime.now()
    shift_end_time = datetime.datetime.now() + datetime.timedelta(hours=3)
    shift_num_slots = 5

    @tag("selenium")
    def test_create_shift(self):
        self.login_as_admin()
        self.selenium.get(self.URL_BASE + reverse("shifts:shift_create"))
        self.wait_until_element_present_by_id("shift_form_card")
        self.fill_shift_create_form()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.check_shift_detail_page()
        # TODO Théo 20.05.21 Check that the shift appears in the dashboard

    def fill_shift_create_form(self):
        self.selenium.find_element_by_id("id_name").send_keys(self.shift_name)

        field_start_date = self.selenium.find_element_by_id("id_start_time")
        field_start_date.clear()
        field_start_date.send_keys(self.shift_start_time.strftime("%m/%d/%Y %H:%M"))

        field_end_date = self.selenium.find_element_by_id("id_end_time")
        field_end_date.clear()
        field_end_date.send_keys(self.shift_end_time.strftime("%m/%d/%Y %H:%M"))

        field_num_slots = self.selenium.find_element_by_id("id_num_slots")
        field_num_slots.clear()
        field_num_slots.send_keys(self.shift_num_slots)

        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

    def check_shift_detail_page(self):
        self.assertEqual(
            self.selenium.find_element_by_id("shift_name").text,
            self.shift_name,
        )
        formatted_time = self.shift_start_time.strftime("%d.%m.%Y, %H:%M")
        formatted_time += " - " + self.shift_end_time.strftime("%H:%M")
        self.assertEqual(
            self.selenium.find_element_by_id("shift_time").text,
            formatted_time,
        )
        self.assertEqual(
            self.selenium.find_element_by_xpath(
                "//*[@id='attendance_table']/tbody/tr[{0}]/td[1]/h5".format(
                    self.shift_num_slots
                )
            ).text,
            "#" + str(self.shift_num_slots),
        )

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
        shift_id = self.check_shift_detail_page()
        self.selenium.get(self.URL_BASE + reverse("shifts:upcoming_timetable"))
        self.wait_until_element_present_by_id("upcoming-shifts-timetable")
        self.check_shift_in_timetable(shift_id)

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

    def check_shift_detail_page(self) -> int:
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

        shift_id = self.selenium.current_url.split("/")[-2]
        return shift_id

    def check_shift_in_timetable(self, shift_id: int):
        shift_block = self.selenium.find_element_by_id("shift_{0}".format(shift_id))
        self.assertEqual(
            shift_block.find_element_by_class_name("shift-name").text, self.shift_name
        )
        shift_time = (
            self.shift_start_time.time().strftime("%H:%M")
            + " - "
            + self.shift_end_time.time().strftime("%H:%M")
        )
        self.assertEqual(
            shift_block.find_element_by_class_name("shift-time").text, shift_time
        )
        shift_date = self.shift_start_time.date().strftime("%a %d/%m/%y")
        self.assertEqual(
            shift_block.find_element_by_class_name("shift-date").text, shift_date
        )

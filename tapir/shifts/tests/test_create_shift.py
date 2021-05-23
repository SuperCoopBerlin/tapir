import datetime

from django.test import tag
from django.test.testcases import SerializeMixin
from django.urls import reverse

from tapir.utils.tests_utils import TapirSeleniumTestBase


class ShiftTestBase(SerializeMixin, TapirSeleniumTestBase):
    lockfile = __file__
    shift_id = -1
    shift_name = "THE_TEST_SHIFT"


class TestCreateShift(ShiftTestBase):
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
        self.selenium.get(self.URL_BASE + reverse("shifts:upcoming_timetable"))
        self.wait_until_element_present_by_id("upcoming-shifts-timetable")
        self.check_shift_in_timetable()

    def fill_shift_create_form(self):
        self.selenium.find_element_by_id("id_name").send_keys(ShiftTestBase.shift_name)

        field_start_date = self.selenium.find_element_by_id("id_start_time")
        field_start_date.clear()
        field_start_date.send_keys(self.shift_start_time.strftime("%m/%d/%Y %H:%M"))

        field_end_date = self.selenium.find_element_by_id("id_end_time")
        field_end_date.clear()
        field_end_date.send_keys(self.shift_end_time.strftime("%m/%d/%Y %H:%M"))

        field_num_slots = self.selenium.find_element_by_id("id_num_slots")
        field_num_slots.clear()
        field_num_slots.send_keys(self.shift_num_slots)

        self.selenium.find_element_by_xpath('//button[text() = "Save"]').click()

    def check_shift_detail_page(self) -> int:
        self.assertEqual(
            self.selenium.find_element_by_id("shift_name").text,
            ShiftTestBase.shift_name,
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

        ShiftTestBase.shift_id = self.selenium.current_url.split("/")[-2]

    def check_shift_in_timetable(self):
        shift_block = self.selenium.find_element_by_id(
            "shift_{0}".format(ShiftTestBase.shift_id)
        )
        self.assertEqual(
            shift_block.find_element_by_class_name("shift-name").text,
            ShiftTestBase.shift_name,
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


class TestEditShift(ShiftTestBase):
    @tag("selenium")
    def test_edit_shift(self):
        self.login_as_admin()
        self.selenium.get(self.URL_BASE + reverse("shifts:upcoming_timetable"))
        self.wait_until_element_present_by_id("upcoming-shifts-timetable")
        self.selenium.find_element_by_id(
            "shift_{0}".format(ShiftTestBase.shift_id)
        ).click()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_element_by_xpath('//button[text()="Edit"]').click()
        self.wait_until_element_present_by_id("shift_form_card")
        new_name = ShiftTestBase.shift_name + " EDITED"
        self.selenium.find_element_by_id("id_name").clear()
        self.selenium.find_element_by_id("id_name").send_keys(new_name)
        self.selenium.find_element_by_xpath('//button[text() = "Save"]').click()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.assertEqual(self.selenium.find_element_by_id("shift_name").text, new_name)

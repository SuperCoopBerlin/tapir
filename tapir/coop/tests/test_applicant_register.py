import json
import os
import pathlib

from django.test import tag
from django.urls import reverse

from tapir.accounts.templatetags.accounts import format_phone_number
from tapir.utils.json_user import JsonUser
from tapir.utils.tests_utils import TapirUserTestBase


class ApplicantTestBase(TapirUserTestBase):
    @staticmethod
    def get_created_user(file_name: str) -> JsonUser:
        path_to_json_file = os.path.join(
            pathlib.Path(__file__).parent.absolute(), file_name
        )
        file = open(path_to_json_file, encoding="UTF-8")
        json_string = file.read()
        file.close()
        return JsonUser(json.loads(json_string)["results"][0])

    def fill_draftuser_form(self, user: JsonUser):
        self.wait_until_element_present_by_id("id_first_name")
        self.selenium.find_element_by_id("id_first_name").send_keys(user.first_name)
        self.selenium.find_element_by_id("id_last_name").send_keys(user.last_name)
        self.selenium.find_element_by_id("id_email").send_keys(user.email)
        self.selenium.find_element_by_id("id_phone_number").send_keys(user.phone_number)

        self.fill_date_field("id_birthdate", user.birthdate)
        self.selenium.find_element_by_id("id_street").send_keys(user.street)
        self.selenium.find_element_by_id("id_street_2").send_keys(user.street_2)
        self.selenium.find_element_by_id("id_postcode").send_keys(user.postcode)
        self.selenium.find_element_by_id("id_city").send_keys(user.city)

        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

    def check_draftuser_details(self, user: JsonUser):
        self.wait_until_element_present_by_id("draft_user_detail_card")

        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_display_name").text,
            user.get_display_name(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_email").text, user.email
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_phone_number").text,
            format_phone_number(user.phone_number),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_birthdate").text,
            user.birthdate.strftime("%d.%m.%Y"),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_address").text,
            user.get_display_address(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_member_type").text,
            "Active",
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_ratenzahlung").text,
            "No",
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_num_shares").text, "1"
        )

    def go_to_applicant_detail_page(self, user: JsonUser):
        self.selenium.get(self.live_server_url + reverse("coop:draftuser_list"))
        self.wait_until_element_present_by_id("applicants_table")
        user_rows = self.selenium.find_element_by_id(
            "applicants_table"
        ).find_elements_by_xpath("//tbody//tr[./td[. = '" + user.email + "']]")
        self.assertEqual(len(user_rows), 1)
        user_rows[0].find_element_by_tag_name("a").click()
        self.wait_until_element_present_by_id("draft_user_detail_card")


class TestApplicantRegister(ApplicantTestBase):
    @tag("selenium")
    def test_applicant_register(self):
        # An external user registers themselves as an Applicant
        self.selenium.get(self.live_server_url + reverse("coop:draftuser_register"))
        self.logout_if_necessary()

        user = self.get_created_user("test_applicant_register.json")
        self.fill_draftuser_form(user)
        self.wait_until_element_present_by_id("draft_user_registration_confirmed")
        self.login_as_admin()
        self.go_to_applicant_detail_page(user)
        self.check_draftuser_details(user)

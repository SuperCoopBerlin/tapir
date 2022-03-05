from django.test import tag
from django.urls import reverse

from tapir.accounts.templatetags.accounts import format_phone_number
from tapir.coop.tests.test_applicant_register import ApplicantTestBase
from tapir.utils.json_user import JsonUser


class TestApplicantToTapirUser(ApplicantTestBase):
    json_file = "test_applicant_create.json"

    @tag("selenium")
    def test_applicant_to_tapir_user(self):
        self.subtest_create_applicant()
        self.subtest_applicant_to_share_owner()
        self.subtest_edit_share_owner()
        self.subtest_create_tapir_user_from_share_owner()

    def subtest_create_applicant(self):
        # A coop member creates an Applicant (for example at the Welcome desk)
        self.selenium.get(self.live_server_url)
        user = self.get_member_office_user()
        self.login(user.get_username(), user.get_username())
        self.selenium.get(self.live_server_url + reverse("coop:draftuser_create"))

        user = self.get_created_user(self.json_file)
        self.fill_draftuser_form(user)
        self.wait_until_element_present_by_id("draft_user_detail_card")
        self.check_draftuser_details(user)

    def subtest_applicant_to_share_owner(self):
        # A coop member transforms a draft user into an investing member
        self.selenium.get(self.live_server_url)
        user = self.get_member_office_user()
        self.login(user.get_username(), user.get_username())

        user = self.get_created_user(self.json_file)
        self.go_to_applicant_detail_page(user)
        self.selenium.find_element_by_id(
            "button_marker_membership_agreement_signed"
        ).click()
        self.wait_until_element_present_by_id("button_create_share_owner")
        self.selenium.find_element_by_id("button_create_share_owner").click()
        self.wait_until_element_present_by_id("share_owner_detail_card")
        self.check_share_owner_details(user)

        # Make sure that the DraftUser is deleted after the ShareOwner has been created
        self.selenium.get(self.live_server_url + reverse("coop:draftuser_list"))
        self.wait_until_element_present_by_id("applicants_table")
        user_rows = self.selenium.find_element_by_id(
            "applicants_table"
        ).find_elements_by_xpath("//tbody//tr[./td[. = '" + user.email + "']]")
        self.assertEqual(len(user_rows), 0)

    def subtest_edit_share_owner(self):
        # A coop member edits the name of a share owner
        self.selenium.get(self.live_server_url)
        user = self.get_member_office_user()
        self.login(user.get_username(), user.get_username())

        user = self.get_created_user(self.json_file)
        self.go_to_share_owner_detail_page(user)
        name_before = user.first_name
        user.first_name = "an edited first name"
        self.set_user_first_name(user)
        self.check_share_owner_details(user)
        self.go_to_share_owner_detail_page(user)
        user.first_name = name_before
        self.set_user_first_name(user)
        self.check_share_owner_details(user)

    def set_user_first_name(self, user: JsonUser):
        self.selenium.find_element_by_id("edit_share_owner_button").click()
        first_name_field = self.selenium.find_element_by_id("id_first_name")
        first_name_field.clear()
        first_name_field.send_keys(user.first_name)
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()
        self.wait_until_element_present_by_id("share_owner_detail_card")

    def subtest_create_tapir_user_from_share_owner(self):
        user = self.get_member_office_user()
        self.login(user.get_username(), user.get_username())

        user = self.get_created_user(self.json_file)
        self.go_to_share_owner_detail_page(user)
        self.selenium.find_element_by_id("create_tapir_user_button").click()
        self.wait_until_element_present_by_id("share_owner_to_tapir_user_card")
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()
        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.go_to_tapir_user_detail_page(user)
        self.check_tapir_user_details(user)

    def go_to_share_owner_detail_page(self, user: JsonUser):
        self.go_to_detail_page(user)
        self.wait_until_element_present_by_id("share_owner_detail_card")

    def go_to_tapir_user_detail_page(self, user: JsonUser):
        self.go_to_detail_page(user)
        self.wait_until_element_present_by_id("tapir_user_detail_card")

    def go_to_detail_page(self, user: JsonUser):
        self.selenium.get(self.live_server_url + reverse("coop:shareowner_list"))
        self.wait_until_element_present_by_id("share_owner_table")

        name_search_field = self.selenium.find_element_by_id("id_display_name")
        name_search_field.send_keys(user.get_display_name())
        self.selenium.find_element_by_class_name("filter-button").click()

    def check_share_owner_details(self, user: JsonUser):
        self.go_to_share_owner_detail_page(user)

        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_display_name").text,
            user.get_display_name(),
        )
        self.assertEqual(
            self.selenium.find_element_by_xpath(
                "//*[@id='share_owner_status']/span"
            ).text,
            "Active",
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_email").text,
            user.email,
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_phone_number").text,
            format_phone_number(user.phone_number),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_birthdate").text,
            user.get_birthdate_display(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_address").text,
            user.get_display_address(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_num_shares").text,
            "1",
        )

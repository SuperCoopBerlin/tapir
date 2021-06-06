from django.test import tag
from django.urls import reverse

from tapir.coop.tests.test_applicant_register import ApplicantTestBase
from django.test.testcases import SerializeMixin


class ApplicantToTapirUserMixin(SerializeMixin):
    lockfile = __file__
    json_file = "test_applicant_create.json"


class TestApplicantCreate(ApplicantTestBase, ApplicantToTapirUserMixin):
    @tag("selenium")
    def test_applicant_create(self):
        # A coop member creates an Applicant (for example at the Welcome desk)
        self.selenium.get(self.URL_BASE)
        self.login_as_admin()
        self.selenium.get(self.URL_BASE + reverse("coop:draftuser_create"))

        user = self.get_test_user(self.json_file)
        self.fill_draftuser_form(user)
        self.wait_until_element_present_by_id("draft_user_detail_card")
        self.check_draftuser_details(user)


class TestApplicantToShareOwner(ApplicantTestBase, ApplicantToTapirUserMixin):
    @tag("selenium")
    def test_applicant_to_share_owner(self):
        # A coop member transforms a draft user into an investing member
        self.selenium.get(self.URL_BASE)
        self.login_as_admin()

        user = self.get_test_user(self.json_file)
        self.go_to_applicant_detail_page(user)
        self.selenium.find_element_by_id(
            "button_marker_membership_agreement_signed"
        ).click()
        self.wait_until_element_present_by_id("button_create_share_owner")
        self.selenium.find_element_by_id("button_create_share_owner").click()
        self.wait_until_element_present_by_id("share_owner_detail_card")

        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_display_name").text,
            user.get_display_name(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_status").text,
            "Active Member",
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_email").text,
            user.email,
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

from django.test import tag
from django.urls import reverse

from tapir.utils.tests_utils import TapirSeleniumTestBase, TapirUserTestBase


class AccountsStandardUserDetailPage(TapirUserTestBase):
    @tag("selenium")
    def test_standard_user_detail_page(self):
        user = self.get_standard_user()
        self.login(user.get_username(), user.get_username())
        self.selenium.get(self.live_server_url + reverse("accounts:user_me"))
        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.check_tapir_user_details(user)

        repeated_shifts = self.selenium.find_elements_by_class_name("repeated-shift")
        self.assertEqual(len(repeated_shifts), 1)
        self.assertEqual(repeated_shifts[0].text, "Supermarket Friday 12:00 (Week D)")

        self.assertFalse(self.does_element_exist_by_id("tapir_user_edit_button"))
        self.assertFalse(self.does_element_exist_by_id("share_owner_edit_buttons"))
        self.assertFalse(self.does_element_exist_by_id("add_note_button"))
        self.assertFalse(
            self.does_element_exist_by_class_name("unregister-repeated-shift-button")
        )

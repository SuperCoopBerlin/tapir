from django.test import tag
from django.urls import reverse
from selenium.webdriver.support.ui import Select

from tapir.coop.models import MemberStatus
from tapir.utils.json_user import JsonUser
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TapirMemberListFilterBase(TapirSeleniumTestBase):
    def check_member_list_filter(
        self,
        dropdown_id: str,
        dropdown_value: str,
        included_users: list[JsonUser],
        excluded_users: list[JsonUser],
    ):
        self.login_as_admin()
        self.selenium.get(self.live_server_url + reverse("coop:shareowner_list"))
        self.wait_until_element_present_by_id("share_owner_table")

        Select(self.selenium.find_element_by_id(dropdown_id)).select_by_value(
            dropdown_value
        )
        self.selenium.find_element_by_class_name("filter-button").click()

        self.wait_until_element_present_by_id("share_owner_table")
        for user in included_users:
            self.assertTrue(
                self.is_user_in_filtered_list(user),
                f"User {user.get_username()} should be in the list of users filtered by {dropdown_id}:{dropdown_value} but isn't.",
            )

        for user in excluded_users:
            self.assertFalse(
                self.is_user_in_filtered_list(user),
                f"User {user.get_username()} should not be in the list of users filtered by {dropdown_id}:{dropdown_value} but is.",
            )

    def is_user_in_filtered_list(self, user: JsonUser) -> bool:
        user_links = self.selenium.find_element_by_id(
            "share_owner_table"
        ).find_elements_by_xpath("//a[text() = '" + user.get_display_name() + "']")
        return len(user_links) == 1


class TestStarnextFilter(TapirMemberListFilterBase):
    @tag("selenium")
    def test_startnext_filter(self):
        included_users = [self.get_test_user("elia.fontai")]
        excluded_users = [self.get_test_user("nicolas.vicente")]
        self.check_member_list_filter(
            "id_from_startnext", "true", included_users, excluded_users
        )


class TestWelcomeSessionFilter(TapirMemberListFilterBase):
    @tag("selenium")
    def test_welcome_session_filter(self):
        included_users = [self.get_test_user("nicolas.vicente")]
        excluded_users = [self.get_test_user("carmelo.rodriguez")]
        self.check_member_list_filter(
            "id_attended_welcome_session", "true", included_users, excluded_users
        )


class TestRatenzahlungFilter(TapirMemberListFilterBase):
    @tag("selenium")
    def test_ratenzahlung_filter(self):
        included_users = [self.get_test_user("charlie.legrand")]
        excluded_users = [self.get_test_user("roberto.cortes")]
        self.check_member_list_filter(
            "id_ratenzahlung", "true", included_users, excluded_users
        )


class TestStatusFilter(TapirMemberListFilterBase):
    @tag("selenium")
    def test_status_filter(self):
        active_user = self.get_test_user("roberto.cortes")
        investing_user = self.get_test_user("encarnacion.torres")
        sold_user = self.get_test_user("gonca.kuzucu")

        included_users = [sold_user]
        excluded_users = [active_user, investing_user]
        self.check_member_list_filter(
            "id_status", MemberStatus.SOLD, included_users, excluded_users
        )

        included_users = [investing_user]
        excluded_users = [active_user, sold_user]
        self.check_member_list_filter(
            "id_status", MemberStatus.INVESTING, included_users, excluded_users
        )

        included_users = [active_user]
        excluded_users = [sold_user, investing_user]
        self.check_member_list_filter(
            "id_status", MemberStatus.ACTIVE, included_users, excluded_users
        )

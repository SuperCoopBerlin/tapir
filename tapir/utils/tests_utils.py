import json
import os
import pathlib
import socket

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase, override_settings
from django.urls import reverse
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from tapir.accounts.templatetags.accounts import format_phone_number
from tapir.utils.json_user import JsonUser


@override_settings(ALLOWED_HOSTS=["*"])
class TapirSeleniumTestBase(StaticLiveServerTestCase):
    DEFAULT_TIMEOUT = 5
    selenium: WebDriver
    test_users: [] = None
    fixtures = ["admin_account.json", "test_data.json"]
    host = "0.0.0.0"  # Bind to 0.0.0.0 to allow external access

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.selenium = webdriver.Remote(
            command_executor=f"http://selenium:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.FIREFOX,
        )
        cls.selenium.maximize_window()
        cls.selenium.implicitly_wait(cls.DEFAULT_TIMEOUT)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def login(self, username: str, password: str):
        self.selenium.get(self.live_server_url + reverse("login"))
        login_card = self.selenium.find_element_by_id("login-card")
        login_card.find_element_by_id("id_username").send_keys(username)
        login_card.find_element_by_id("id_password").send_keys(password)
        login_card.find_element_by_tag_name("button").click()
        self.wait_until_element_present_by_id("logout")

    def login_as_admin(self):
        self.login("admin", "admin")

    def get_test_user(self, searched_username: str) -> JsonUser:
        if self.test_users is None:
            path_to_json_file = os.path.join(
                pathlib.Path(__file__).parent.absolute(),
                "management",
                "commands",
                "test_users.json",
            )
            file = open(path_to_json_file, encoding="UTF-8")
            json_string = file.read()
            file.close()
            self.test_users = json.loads(json_string)["results"]

        for parsed_user in self.test_users:
            json_user = JsonUser(parsed_user)
            if json_user.get_username() == searched_username:
                return json_user

        raise Exception("No test user found")

    def get_vorstand_user(self) -> JsonUser:
        return self.get_test_user("ariana.perrin")

    def get_member_office_user(self) -> JsonUser:
        return self.get_test_user("roberto.cortes")

    def get_standard_user(self) -> JsonUser:
        return self.get_test_user("nicolas.vicente")

    def logout_if_necessary(self):
        url_before = self.selenium.current_url

        if not self.does_element_exist_by_id("logout"):
            return
        logout_button = self.selenium.find_element_by_id("logout")
        logout_button.click()
        self.wait_until_element_present_by_id("login-card")

        self.selenium.get(url_before)

    def does_element_exist_by_id(self, html_id: str) -> bool:
        try:
            self.selenium.implicitly_wait(1)
            self.selenium.find_element_by_id(html_id)
        except NoSuchElementException:
            return False
        finally:
            self.selenium.implicitly_wait(self.DEFAULT_TIMEOUT)

        return True

    def does_element_exist_by_class_name(self, class_name: str) -> bool:
        return len(self.selenium.find_elements_by_class_name(class_name)) > 0

    def wait_until_element_present_by_id(self, html_id: str):
        try:
            WebDriverWait(self.selenium, self.DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.ID, html_id))
            )
        except TimeoutException:
            self.fail("Missing element with ID " + html_id)


class TapirUserTestBase(TapirSeleniumTestBase):
    def check_tapir_user_details(self, user: JsonUser):
        self.assertEqual(
            self.selenium.find_element_by_id("tapir_user_display_name").text,
            user.get_display_name(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("tapir_user_username").text,
            user.get_username(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("tapir_user_email").text,
            user.email,
        )
        self.assertEqual(
            self.selenium.find_element_by_id("tapir_user_phone_number").text,
            format_phone_number(user.phone_number),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("tapir_user_birthdate").text,
            user.get_birthdate_display(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("tapir_user_address").text,
            user.get_display_address(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_status").text,
            "Active",
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_num_shares").text,
            str(user.num_shares),
        )


class LdapEnabledTestCase(TestCase):
    databases = {"ldap", DEFAULT_DB_ALIAS}

import datetime
import json
import os
import pathlib
import socket
from typing import Type

import factory.random
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.mail import EmailMessage
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from tapir.accounts.models import TapirUser
from tapir.accounts.templatetags.accounts import format_phone_number
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.utils.expection_utils import TapirException
from tapir.utils.json_user import JsonUser

TAPIR_SELENIUM_BASE_FIXTURES = ["admin_account.json", "test_data.json"]


@override_settings(ALLOWED_HOSTS=["*"])
class TapirSeleniumTestBase(StaticLiveServerTestCase):
    DEFAULT_TIMEOUT = 5
    selenium: WebDriver
    test_users: [] = None
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES
    host = "0.0.0.0"  # Bind to 0.0.0.0 to allow external access

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.selenium = webdriver.Remote(
            command_executor="http://selenium:4444/wd/hub",
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
        login_card = self.selenium.find_element(By.ID, "login-card")
        login_card.find_element(By.ID, "id_username").send_keys(username)
        login_card.find_element(By.ID, "id_password").send_keys(password)
        login_card.find_element(By.TAG_NAME, "button").click()
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
            json_file = open(path_to_json_file, encoding="UTF-8")
            json_string = json_file.read()
            json_file.close()
            self.test_users = json.loads(json_string)["results"]

        for parsed_user in self.test_users:
            json_user = JsonUser(parsed_user)
            if json_user.get_username() == searched_username:
                return json_user

        raise TapirException("No test user found")

    def get_vorstand_user(self) -> JsonUser:
        return self.get_test_user("roberto.cortes")

    def get_member_office_user(self) -> JsonUser:
        return self.get_test_user("sasha.hubert")

    def get_standard_user(self) -> JsonUser:
        return self.get_test_user("nicolas.vicente")

    def logout_if_necessary(self):
        url_before = self.selenium.current_url

        if not self.does_element_exist_by_id("logout"):
            return
        logout_button = self.selenium.find_element(By.ID, "logout")
        logout_button.click()
        self.wait_until_element_present_by_id("login-card")

        self.selenium.get(url_before)

    def does_element_exist_by_id(self, html_id: str) -> bool:
        try:
            self.selenium.implicitly_wait(1)
            self.selenium.find_element(By.ID, html_id)
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

    def wait_until_element_present_by_class_name(self, html_class: str):
        try:
            WebDriverWait(self.selenium, self.DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.CLASS_NAME, html_class))
            )
        except TimeoutException:
            self.fail("Missing element with class " + html_class)

    def go_to_user_page(self, user_display_name: str):
        self.selenium.get(self.live_server_url + reverse("coop:shareowner_list"))

        member_search = self.selenium.find_element(By.ID, "member_search")
        member_search.send_keys(user_display_name)
        member_search.send_keys(Keys.ENTER)

        self.wait_until_element_present_by_id("user_coop_info_card")

    @staticmethod
    def is_button_disabled(button: WebElement):
        return "disabled" in button.get_attribute("class")

    def fill_date_field(self, element_id, date: datetime.date):
        # Somehow send_keys doesn't work for <input type="date"> in Firefox
        self.selenium.execute_script(
            f"document.getElementById('{element_id}').value = '"
            + date.strftime("%Y-%m-%d")
            + "';"
        )


class TapirUserTestBase(TapirSeleniumTestBase):
    def check_tapir_user_details(self, user: JsonUser):
        self.assertEqual(
            self.selenium.find_element(By.ID, "tapir_user_display_name").text,
            user.get_display_name(),
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "tapir_user_username").text,
            user.get_username(),
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "tapir_user_email").text,
            user.email,
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "tapir_user_phone_number").text,
            format_phone_number(user.phone_number),
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "tapir_user_birthdate").text,
            user.get_birthdate_display(),
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "tapir_user_address").text,
            user.get_display_address(),
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "share_owner_status").text,
            "Active",
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "share_owner_num_shares").text,
            str(user.num_shares),
        )


class LdapEnabledTestCase(TestCase):
    databases = {"ldap", DEFAULT_DB_ALIAS}


class TapirFactoryTestBase(LdapEnabledTestCase):
    client: Client

    def setUp(self) -> None:
        factory.random.reseed_random(self.__class__.__name__)
        self.client = Client()

    def login_as_user(self, user: TapirUser):
        success = self.client.login(username=user.username, password=user.username)
        self.assertTrue(success, f"User {user.username} should be able to log in.")

    def login_as_vorstand(self) -> TapirUser:
        user = TapirUserFactory.create(is_in_vorstand=True)
        self.login_as_user(user)
        return user

    def login_as_member_office_user(self) -> TapirUser:
        user = TapirUserFactory.create(is_in_member_office=True)
        self.login_as_user(user)
        return user

    def login_as_normal_user(self) -> TapirUser:
        user = TapirUserFactory.create(is_in_member_office=False)
        self.login_as_user(user)
        return user

    def login_as_shift_manager(self) -> TapirUser:
        user = TapirUserFactory.create(is_shift_manager=True)
        self.login_as_user(user)
        return user


class TapirEmailTestBase(TestCase):
    def assertEmailOfClass_GotSentTo(
        self,
        expected_class: Type[TapirEmailBase],
        target_email_address: str,
        mail: EmailMessage,
    ):
        self.assertEqual([target_email_address], mail.to)
        self.assertInHTML(
            f"<meta name='email_id' content='{expected_class.get_unique_id()}' />",
            mail.body,
        )

    def assertEmailAttachmentIsAPdf(self, attachment):
        attachment_name = attachment[0]
        self.assertEqual(".pdf", attachment_name[-4:])
        attachment_type = attachment[2]
        self.assertEqual(CONTENT_TYPE_PDF, attachment_type)

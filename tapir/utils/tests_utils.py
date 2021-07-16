import socket

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import DEFAULT_DB_ALIAS
from django.urls import reverse
from django.test import TestCase, override_settings
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@override_settings(ALLOWED_HOSTS=["*"])
class TapirSeleniumTestBase(StaticLiveServerTestCase):
    DEFAULT_TIMEOUT = 5
    selenium: WebDriver
    fixtures = ["accounts.json"]
    host = "0.0.0.0"  # Bind to 0.0.0.0 to allow external access

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.selenium = webdriver.Remote(
            command_executor=f"http://selenium:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.FIREFOX,
        )
        cls.selenium.set_window_position(-1920, 0)
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

    def login_as_vorstand(self):
        self.login("ariana.perrin", "ariana.perrin")

    def login_as_member_office(self):
        self.login("roberto.cortes", "roberto.cortes")

    def login_as_standard_user(self):
        self.login("nicolas.vicente", "nicolas.vicente")

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

    def wait_until_element_present_by_id(self, html_id: str):
        try:
            WebDriverWait(self.selenium, self.DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.ID, html_id))
            )
        except TimeoutException:
            self.fail("Missing element with ID " + html_id)


class LdapEnabledTestCase(TestCase):
    databases = {"ldap", DEFAULT_DB_ALIAS}

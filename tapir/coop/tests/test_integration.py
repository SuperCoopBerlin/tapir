import json
import os
import pathlib

from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test import tag
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tapir.utils.json_user import JsonUser


class AccountsIntegrationTests(LiveServerTestCase):
    DEFAULT_TIMEOUT = 5
    selenium: WebDriver

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        firefox_options = webdriver.FirefoxOptions()
        # firefox_options.headless = True
        cls.selenium = webdriver.Firefox(firefox_options=firefox_options)
        cls.selenium.set_window_position(-1920, 0)
        cls.selenium.maximize_window()
        cls.selenium.implicitly_wait(cls.DEFAULT_TIMEOUT)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    @tag("selenium")
    def test_register_draft_user(self):
        self.selenium.get("http://localhost:8000/coop/user/draft/register")
        self.logout_if_necessary()

        path_to_json_file = os.path.join(
            pathlib.Path(__file__).parent.absolute(), "draftuser_valid.json"
        )
        file = open(path_to_json_file, encoding="UTF-8")
        json_string = file.read()
        file.close()
        user = JsonUser(json.loads(json_string)["results"][0])

        self.wait_until_element_present_by_id("id_first_name")

        self.selenium.find_element_by_id("id_first_name").send_keys(user.first_name)
        self.selenium.find_element_by_id("id_last_name").send_keys(user.last_name)
        self.selenium.find_element_by_id("id_email").send_keys(user.email)
        self.selenium.find_element_by_id("id_phone_number").send_keys(user.phone_number)

        # Somehow send_keys doesn't work for <input type="date"> in Firefox
        self.selenium.execute_script(
            "document.getElementById('id_birthdate').value = '"
            + user.get_date_of_birth_str_for_input_field()
            + "';"
        )

        self.selenium.find_element_by_id("id_street").send_keys(user.street)
        self.selenium.find_element_by_id("id_street_2").send_keys(user.street_2)
        self.selenium.find_element_by_id("id_postcode").send_keys(user.postcode)
        self.selenium.find_element_by_id("id_city").send_keys(user.city)

        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

        WebDriverWait(self.selenium, self.DEFAULT_TIMEOUT).until(
            lambda driver: driver.find_element_by_id(
                "draft_user_registration_confirmed"
            )
        )

        self.login_as_admin()
        self.selenium.get("http://localhost:8000/coop/user/draft/")
        self.wait_until_element_present_by_id("applicants_table")
        user_row = self.selenium.find_element_by_id(
            "applicants_table"
        ).find_element_by_xpath("//tbody//tr[./td[. = '" + user.email + "']]")
        user_row.find_element_by_tag_name("a").click()
        self.wait_until_element_present_by_id("draft_user_detail_card")

        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_display_name").text,
            user.get_display_name(),
        )

        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_username").text,
            user.get_username(),
        )

        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_email").text, user.email
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_birthdate").text,
            user.date_of_birth.strftime("%d.%m.%Y"),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_address").text,
            user.get_complete_address(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("draft_user_num_shares").text, "1"
        )

    def logout_if_necessary(self):
        url_before = self.selenium.current_url

        if not self.does_element_exist_by_id("logout"):
            return
        logout_button = self.selenium.find_element_by_id("logout")
        logout_button.click()
        self.wait_until_element_present_by_id("login-card")

        self.selenium.get(url_before)

    def login_as_admin(self):
        self.selenium.get("http://localhost:8000/accounts/login/")
        login_card = self.selenium.find_element_by_id("login-card")
        login_card.find_element_by_id("id_username").send_keys("admin")
        login_card.find_element_by_id("id_password").send_keys("admin")
        login_card.find_element_by_tag_name("button").click()
        self.wait_until_element_present_by_id("logout")

    def wait_until_element_present_by_id(self, html_id: str):
        WebDriverWait(self.selenium, self.DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, html_id))
        )

    def does_element_exist_by_id(self, html_id: str) -> bool:
        try:
            self.selenium.implicitly_wait(1)
            self.selenium.find_element_by_id(html_id)
        except NoSuchElementException:
            return False
        finally:
            self.selenium.implicitly_wait(self.DEFAULT_TIMEOUT)

        return True

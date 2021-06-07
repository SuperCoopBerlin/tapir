from django.contrib.staticfiles.testing import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TapirSeleniumTestBase(LiveServerTestCase):
    URL_BASE = "http://localhost:8000/"
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

    def login_as_admin(self):
        self.selenium.get("http://localhost:8000/accounts/login/")
        login_card = self.selenium.find_element_by_id("login-card")
        login_card.find_element_by_id("id_username").send_keys("admin")
        login_card.find_element_by_id("id_password").send_keys("admin")
        login_card.find_element_by_tag_name("button").click()
        self.wait_until_element_present_by_id("logout")

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
                EC.presence_of_element_located((By.ID, html_id))
            )
        except TimeoutException:
            self.fail("Missing element with ID " + html_id)

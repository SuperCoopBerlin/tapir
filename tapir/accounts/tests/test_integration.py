from django.test import tag
from selenium.webdriver.common.by import By

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirSeleniumTestBase


class AccountsIntegrationTests(TapirSeleniumTestBase):
    @tag("selenium")
    def test_login(self):
        self.selenium.get(self.live_server_url)
        self.logout_if_necessary()
        user = TapirUserFactory.create()
        self.login(user.username, user.username)
        self.assertIsNotNone(self.selenium.find_element(By.ID, "logout"))

    @tag("selenium")
    def test_redirect_to_login_page(self):
        self.selenium.get(self.live_server_url)
        self.logout_if_necessary()
        self.selenium.get(f"{self.live_server_url}/coop/member/")
        url = str(self.selenium.current_url)
        self.assertTrue("/accounts/login/" in url)

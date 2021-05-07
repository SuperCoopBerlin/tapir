from django.test import tag

from tapir.utils.tests_utils import TapirSeleniumTestBase


class AccountsIntegrationTests(TapirSeleniumTestBase):
    @tag("selenium")
    def test_login_as_admin(self):
        self.selenium.get("http://localhost:8000")
        self.logout_if_necessary()
        self.login_as_admin()
        self.assertIsNotNone(self.selenium.find_element_by_id("logout"))

    @tag("selenium")
    def test_redirect_to_login_page(self):
        self.selenium.get("http://localhost:8000")
        self.logout_if_necessary()
        self.selenium.get("http://localhost:8000/coop/member/")
        url = str(self.selenium.current_url)
        self.assertTrue("/accounts/login/" in url)

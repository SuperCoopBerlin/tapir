import datetime
import json
import os
import pathlib
import socket
from http import HTTPStatus
from typing import Type
from unittest.mock import patch

import factory.random
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.mail import EmailMessage
from django.test import TestCase, override_settings, Client, SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwnership
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.models import (
    ShiftAttendanceTemplate,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.expection_utils import TapirException
from tapir.utils.json_user import JsonUser
from tapir.utils.shortcuts import get_admin_ldap_connection, set_group_membership


@override_settings(ALLOWED_HOSTS=["*"])
class TapirSeleniumTestBase(StaticLiveServerTestCase):
    DEFAULT_TIMEOUT = 5
    selenium: WebDriver
    test_users: [] = None
    host = "0.0.0.0"  # Bind to 0.0.0.0 to allow external access

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.selenium = webdriver.Remote(
            command_executor="http://selenium:4444/wd/hub",
            options=webdriver.FirefoxOptions(),
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


class TapirFactoryTestBase(TestCase):
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

    def login_as_member_office_user(self, **kwargs) -> TapirUser:
        user = TapirUserFactory.create(is_in_member_office=True, **kwargs)
        self.login_as_user(user)
        return user

    def login_as_normal_user(self, **kwargs) -> TapirUser:
        user = TapirUserFactory.create(is_in_member_office=False, **kwargs)
        self.login_as_user(user)
        return user

    def login_as_shift_manager(self) -> TapirUser:
        user = TapirUserFactory.create(is_shift_manager=True)
        self.login_as_user(user)
        return user

    def login_as_accounting_team(self) -> TapirUser:
        user = TapirUserFactory.create(is_in_accounting_team=True)
        self.login_as_user(user)
        return user

    def login_as_employee(self) -> TapirUser:
        user = TapirUserFactory.create(is_employee=True)
        self.login_as_user(user)
        return user

    def tearDown(self):
        connection = get_admin_ldap_connection()
        for tapir_user in TapirUser.objects.all():
            connection.delete_s(tapir_user.build_ldap_dn())

    def assertStatusCode(self, response, expected_status_code):
        try:
            content_decoded = response.content.decode()
        except UnicodeDecodeError:
            content_decoded = "Unable to decode content."

        self.assertEqual(
            expected_status_code,
            response.status_code,
            f"Unexpected status code, response content : {content_decoded}",
        )


class TapirEmailTestMixin(TestCase):
    def assertEmailOfClass_GotSentTo(
        self,
        expected_class: Type[TapirEmailBuilderBase],
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


def mock_timezone_now(
    test: SimpleTestCase, now: datetime.datetime
) -> datetime.datetime:
    now = timezone.make_aware(now) if timezone.is_naive(now) else now
    patcher = patch("django.utils.timezone.now")
    test.mock_now = patcher.start()
    test.addCleanup(patcher.stop)
    test.mock_now.return_value = now
    return now


class FeatureFlagTestMixin(TestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName=methodName)
        self._enabled_feature_flags = []

    def setUp(self) -> None:
        patcher = patch("tapir.core.models.FeatureFlag.get_flag_value")
        self.mock_get_flag_value = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_get_flag_value.side_effect = (
            lambda flag_name: flag_name in self._enabled_feature_flags
        )

    def given_feature_flag_value(self, flag_name: str, flag_value: bool):
        if flag_value and flag_name not in self._enabled_feature_flags:
            self._enabled_feature_flags.append(flag_name)
        elif not flag_value and flag_name in self._enabled_feature_flags:
            self._enabled_feature_flags.remove(flag_name)


class PermissionTestMixin:
    def get_allowed_groups(self):
        raise NotImplementedError(
            "Children of PermissionTestMixin must implement get_allowed_groups to say which groups should have access to the view."
        )

    def do_request(self):
        raise NotImplementedError(
            "Children of PermissionTestMixin must implement do_request, a function that visits the target view and returns the response."
        )

    def test_accessView_loggedInAsMemberOfGroup_accessAsExpected(self):
        for group in settings.LDAP_GROUPS:
            with self.subTest(group=group):
                user = TapirUserFactory.create()

                set_group_membership(
                    tapir_users=[user], group_cn=group, is_member_of_group=True
                )
                self.assertEqual(set([group]), user.get_ldap_user().group_names)

                self.login_as_user(user)
                response = self.do_request()
                self.assertStatusCode(
                    response,
                    (
                        HTTPStatus.OK
                        if group in self.get_allowed_groups()
                        else HTTPStatus.FORBIDDEN
                    ),
                )


def create_attendance_template_log_entry_in_the_past(
    log_class, tapir_user, reference_datetime
):
    shift_template = ShiftTemplateFactory.create()
    shift_attendance_template = ShiftAttendanceTemplate.objects.create(
        user=tapir_user, slot_template=shift_template.slot_templates.first()
    )
    kwargs = {
        "actor": None,
        "tapir_user": tapir_user,
        "shift_attendance_template": shift_attendance_template,
    }
    if log_class == DeleteShiftAttendanceTemplateLogEntry:
        kwargs["comment"] = "A test comment"
    log_entry = log_class().populate(**kwargs)
    log_entry.save()
    log_entry.created_date = reference_datetime - datetime.timedelta(days=1)
    log_entry.save()


def create_member_that_can_shop(test, reference_time):
    tapir_user = TapirUserFactory.create(
        share_owner__is_investing=False,
        date_joined=reference_time - datetime.timedelta(hours=1),
    )
    ShareOwnership.objects.update(start_date=reference_time.date())
    test.assertTrue(
        MemberCanShopService.can_shop(tapir_user.share_owner, reference_time)
    )
    return tapir_user


def create_member_that_is_working(test, reference_time):
    tapir_user = TapirUserFactory.create(
        share_owner__is_investing=False,
        date_joined=reference_time - datetime.timedelta(hours=1),
    )
    ShareOwnership.objects.update(start_date=reference_time.date())
    test.assertTrue(
        ShiftExpectationService.is_member_expected_to_do_shifts(
            tapir_user.shift_user_data, reference_time
        )
    )
    return tapir_user

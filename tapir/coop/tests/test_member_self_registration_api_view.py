import datetime
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.core import mail
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.config import feature_flag_self_registration_enabled
from tapir.coop.emails.self_registration_confirmation_mail import (
    SelfRegistrationConfirmationMail,
)
from tapir.coop.models import DraftUser
from tapir.coop.tests.factories import DraftUserFactory, ShareOwnerFactory
from tapir.core.models import FeatureFlag
from tapir.utils.tests_utils import (
    TapirEmailTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestMemberSelfRegistrationView(TapirEmailTestMixin, TapirFactoryTestBase):
    @classmethod
    def setUpTestData(cls):
        FeatureFlag.ensure_flag_exists(feature_flag_self_registration_enabled)
        FeatureFlag.set_flag_value(feature_flag_self_registration_enabled, True)

    @classmethod
    def _build_valid_post_data(cls):
        return {
            "first_name": "Foo",
            "last_name": "Bar",
            "is_company": True,
            "is_investing": False,
            "num_shares": 13,
            "ratenzahlung": True,
            "company_name": "FirmaCorp",
            "usage_name": "Buzz",
            "pronouns": "They/Them",
            "birthdate": "1990-12-22",
            "preferred_language": "en",
            "street": "Test street 28",
            "city": "Test city",
            "postcode": "12345",
            "country": "FR",
            "email": "test@example.com",
            "phone": "0176272674529",
            "client_captcha_response": "test_response",
        }

    @patch("requests.post", autospec=True)
    def test_post_emailAddressAlreadyInUseShareOwner_returnsError(
        self, mock_requests_post: MagicMock
    ):
        post_data = self._build_valid_post_data()
        ShareOwnerFactory.create(email=post_data["email"])
        self._mock_captcha_response(mock_requests_post, success=True)

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.CONFLICT)
        self.assertFalse(DraftUser.objects.exists())
        self.assertEqual(
            "This email address (test@example.com) is already in use",
            response.json(),
        )

    @patch("requests.post", autospec=True)
    def test_post_emailAddressAlreadyInUseTapirUser_returnsError(
        self, mock_requests_post: MagicMock
    ):
        post_data = self._build_valid_post_data()
        TapirUserFactory.create(email=post_data["email"])
        self._mock_captcha_response(mock_requests_post, success=True)

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.CONFLICT)
        self.assertFalse(DraftUser.objects.exists())
        self.assertEqual(
            "This email address (test@example.com) is already in use",
            response.json(),
        )

    @patch("requests.post", autospec=True)
    def test_post_emailAddressAlreadyInUseDraftUser_returnsError(
        self, mock_requests_post: MagicMock
    ):
        post_data = self._build_valid_post_data()
        DraftUserFactory.create(email=post_data["email"])
        self._mock_captcha_response(mock_requests_post, success=True)

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.CONFLICT)
        self.assertEqual(1, DraftUser.objects.count())
        self.assertEqual(
            "This email address (test@example.com) is already in use",
            response.json(),
        )

    @patch("requests.post", autospec=True)
    def test_post_memberTooYoung_returnsError(self, mock_requests_post: MagicMock):
        post_data = self._build_valid_post_data()
        post_data["is_company"] = False
        post_data["birthdate"] = "2003-09-01"
        mock_timezone_now(test=self, now=datetime.datetime(year=2020, month=1, day=1))
        self._mock_captcha_response(mock_requests_post, success=True)

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.UNPROCESSABLE_CONTENT)
        self.assertFalse(DraftUser.objects.exists())
        self.assertEqual("You must be at least 18 years old", response.json())

    def test_post_flagDisabled_returnsError(self):
        FeatureFlag.set_flag_value(feature_flag_self_registration_enabled, False)
        post_data = self._build_valid_post_data()

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)
        self.assertFalse(DraftUser.objects.exists())

    @patch("requests.post", autospec=True)
    def test_post_default_createsDraftUserAndSendsConfirmationMail(
        self, mock_requests_post: MagicMock
    ):
        post_data = self._build_valid_post_data()
        self._mock_captcha_response(mock_requests_post, success=True)

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.CREATED)

        self.assertEqual(1, DraftUser.objects.count())

        self.assertEqual(1, len(mail.outbox))
        self.assertEmailOfClass_GotSentTo(
            expected_class=SelfRegistrationConfirmationMail,
            target_email_address="test@example.com",
            mail=mail.outbox[0],
        )

        draft_user = DraftUser.objects.get()
        self.assertEqual("Foo", draft_user.first_name)
        self.assertEqual("Bar", draft_user.last_name)
        self.assertTrue(draft_user.is_company)
        self.assertFalse(draft_user.is_investing)
        self.assertEqual(13, draft_user.num_shares)
        self.assertTrue(draft_user.ratenzahlung)
        self.assertEqual("FirmaCorp", draft_user.company_name)
        self.assertEqual("Buzz", draft_user.usage_name)
        self.assertEqual("They/Them", draft_user.pronouns)
        self.assertEqual(
            datetime.date(year=1990, month=12, day=22), draft_user.birthdate
        )
        self.assertEqual("Test street 28", draft_user.street)
        self.assertEqual("Test city", draft_user.city)
        self.assertEqual("12345", draft_user.postcode)
        self.assertEqual("FR", draft_user.country)
        self.assertEqual("test@example.com", draft_user.email)
        self.assertEqual("0176272674529", draft_user.phone_number)

    @classmethod
    def _mock_captcha_response(cls, mock_requests_post: MagicMock, success: bool):
        captcha_api_response = MagicMock()
        mock_requests_post.return_value = captcha_api_response
        captcha_api_response.status_code = 200
        captcha_api_response.json.return_value = {"success": success}

    @patch("requests.post", autospec=True)
    def test_post_captchaFails_returnsError(self, mock_requests_post: MagicMock):
        post_data = self._build_valid_post_data()
        ShareOwnerFactory.create(email=post_data["email"])
        self._mock_captcha_response(mock_requests_post, success=False)

        response = self.client.post(
            reverse("coop:member_self_register"), data=post_data
        )

        self.assertStatusCode(response, HTTPStatus.UNPROCESSABLE_CONTENT)
        self.assertFalse(DraftUser.objects.exists())
        self.assertEqual(
            "Captcha failed, try again",
            response.json(),
        )

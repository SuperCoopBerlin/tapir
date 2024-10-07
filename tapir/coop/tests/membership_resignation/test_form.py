import datetime
from http import HTTPStatus
from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)
from django.core.exceptions import ValidationError
from coop.forms import MembershipResignationForm


class TestMembershipResignationForm(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_empty_form(self):
        form = MembershipResignationForm()
        self.assertIn("share_owner", form.fields)
        self.assertIn("resignation_type", form.fields)
        self.assertIn("cancellation_date", form.fields)
        self.assertIn("transferring_shares_to", form.fields)

    def test_validations(self):
        self.assertRaises(
            ValidationError, MembershipResignationForm.validate_duplicates
        )
        self.assertRaises(
            ValidationError, MembershipResignationForm.validate_share_owner
        )
        self.assertRaises(
            ValidationError, MembershipResignationForm.validate_transfer_choice
        )
        self.assertRaises(ValidationError, MembershipResignationForm.validate_if_gifted)

    def test_membershipResignationForm_loggedInAsMemberOffice_accessGranted(self):
        self.login_as_member_office_user()
        resignation_form: MembershipResignationForm = MembershipResignationForm.create()

        response = self.client.get(
            reverse("coop:resign_member_edit", args=[resignation_form.id])
        )
        self.assertStatusCode(response, HTTPStatus.OK)

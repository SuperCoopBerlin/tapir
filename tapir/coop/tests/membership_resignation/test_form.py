import datetime
from http import HTTPStatus
from django.urls import reverse
from django.core.exceptions import ValidationError

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)

from icecream import ic

from tapir.coop.models import MembershipResignation
from tapir.coop.forms import MembershipResignationForm
from tapir.coop.tests.factories import MembershipResignationFactory, ShareOwnerFactory


class TestMembershipResignationForm(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_membershipResignationForm_is_valid(self):
        ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create()
        data = {
            "share_owner": resignation.id,
            "cancellation_reason": resignation.cancellation_reason,
            "cancellation_date": resignation.cancellation_date,
            "resignation_type": resignation.resignation_type,
            "transferring_shares_to": resignation.transferring_shares_to,
            "paid_out": resignation.paid_out,
        }
        form = MembershipResignationForm(data=data)
        self.assertTrue(form.is_valid())
        return form

    def test_validate_shareOwner_function(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        form = MembershipResignationForm(data={"share_owner": resignation.share_owner})
        form.validate_share_owner(resignation.share_owner)
        self.assertIn("share_owner", form.errors.keys())
        self.assertIn(
            "This member is already resigned.",
            form.errors["share_owner"],
        )

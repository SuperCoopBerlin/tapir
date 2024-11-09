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

    def test_isValid_sendingValidData_returnsTrue(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create()
        data = {
            "share_owner": share_owner,
            "cancellation_reason": "A test reason.",
            "cancellation_date": resignation.cancellation_date,
            "resignation_type": resignation.resignation_type,
            "transferring_shares_to": resignation.transferring_shares_to,
            "paid_out": resignation.paid_out,
        }
        form = MembershipResignationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_validate_share_owner_duplicateErrors_isThrown(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        form = MembershipResignationForm(data={"share_owner": resignation.share_owner})
        form.validate_share_owner(resignation.share_owner)
        self.assertIn("share_owner", form.errors.keys())
        self.assertIn(
            "This member is already resigned.",
            form.errors["share_owner"],
        )

    def test_validate_transfer_choice_notChosenError_isThrown(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
        )
        form = MembershipResignationForm(
            data={
                "share_owner": resignation.share_owner,
                "resignation_type": resignation.resignation_type,
                "transferring_shares_to": resignation.transferring_shares_to,
            }
        )
        form.validate_transfer_choice(
            resignation.resignation_type,
            transferring_shares_to=None,
        )
        self.assertIn("transferring_shares_to", form.errors.keys())
        self.assertIn(
            "Please select the member that the shares should be transferred to.",
            form.errors["transferring_shares_to"],
        )
        form.validate_transfer_choice(
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            transferring_shares_to=resignation.transferring_shares_to,
        )
        self.assertIn("transferring_shares_to", form.errors.keys())
        self.assertIn(
            "If the shares don't get transferred to another member, this field should be empty.",
            form.errors["transferring_shares_to"],
        )

    def test_validate_duplicates_errorShareownerAndTransferringSharesToDuplicate_isThrown(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner, transferring_shares_to=share_owner
        )
        form = MembershipResignationForm(
            data={
                "share_owner": resignation.share_owner,
                "transferring_shares_to": resignation.share_owner,
            }
        )
        form.validate_duplicates(
            share_owner=resignation.share_owner,
            transferring_shares_to=resignation.transferring_shares_to,
        )
        self.assertIn("transferring_shares_to", form.errors.keys())
        self.assertIn(
            "Sender and receiver of transferring the share(s) cannot be the same.",
            form.errors["transferring_shares_to"],
        )

    def test_validate_if_gifted_paidOutError_isThrown(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.GIFT_TO_COOP,
        )
        form = MembershipResignationForm(
            data={
                "share_owner": resignation.share_owner,
                "resignation_type": resignation.resignation_type,
            }
        )
        form.validate_if_gifted(
            resignation_type=resignation.resignation_type,
            paid_out=True,
        )
        self.assertIn("paid_out", form.errors.keys())
        self.assertIn(
            "Cannot pay out, because shares have been gifted.",
            form.errors["paid_out"],
        )

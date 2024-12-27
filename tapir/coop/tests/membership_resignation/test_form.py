import datetime

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.forms import MembershipResignationForm
from tapir.coop.models import MembershipResignation
from tapir.coop.tests.factories import MembershipResignationFactory, ShareOwnerFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)


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
            "cancellation_reason_category": MembershipResignation.CancellationReasons.OTHER,
            "cancellation_date": resignation.cancellation_date,
            "resignation_type": resignation.resignation_type,
            "transferring_shares_to": resignation.transferring_shares_to,
            "paid_out": resignation.paid_out,
        }
        form = MembershipResignationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_validateShareOwner_memberIsAlreadyResigned_errorIsAddedToForm(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        form = MembershipResignationForm(data={"share_owner": resignation.share_owner})
        self.assertIn("share_owner", form.errors.keys())
        self.assertIn(
            "This member is already resigned.",
            form.errors["share_owner"],
        )

    def test_validateShareOwner_memberHasNoPreviousResignation_noErrors(self):
        share_owner = ShareOwnerFactory.create()
        form = MembershipResignationForm(data={"share_owner": share_owner})
        form.validate_share_owner(share_owner)
        self.assertNotIn("share_owner", form.errors.keys())

    def test_validateTransferChoice_resignationTypeTransferButNoRecipient_errorIsAddedToForm(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        form = MembershipResignationForm(
            data={
                "share_owner": share_owner,
                "resignation_type": MembershipResignation.ResignationType.TRANSFER,
            }
        )
        self.assertIn("transferring_shares_to", form.errors.keys())
        self.assertIn(
            "Please select the member that the shares should be transferred to.",
            form.errors["transferring_shares_to"],
        )

    def test_validateTransferChoice_resignationTypeNotTransferButRecipientSent_errorIsAddedToForm(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.build(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            transferring_shares_to=ShareOwnerFactory.create(),
        )
        form = MembershipResignationForm(
            data={
                "share_owner": resignation.share_owner,
                "resignation_type": resignation.resignation_type,
                "transferring_shares_to": resignation.transferring_shares_to,
            }
        )
        self.assertIn("transferring_shares_to", form.errors.keys())
        self.assertIn(
            "If the shares don't get transferred to another member, this field should be empty.",
            form.errors["transferring_shares_to"],
        )

    def test_validateGiftingMemberAndReceivingMemberAreNotTheSame_giftingAndReceivingMembersAreTheSame_errorIsAddedToForm(
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
        self.assertIn("transferring_shares_to", form.errors.keys())
        self.assertIn(
            "Sender and receiver of transferring the share(s) cannot be the same.",
            form.errors["transferring_shares_to"],
        )

    def test_validateGiftingMemberAndReceivingMemberAreNotTheSame_giftingAndReceivingMembersAreNotTheSame_noErrorIsAddedToForm(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
        )
        form = MembershipResignationForm(
            data={
                "share_owner": resignation.share_owner,
                "resignation_type": resignation.resignation_type,
                "transferring_shares_to": ShareOwnerFactory.create(),
            }
        )
        self.assertNotIn("transferring_shares_to", form.errors.keys())

    def test_validatePaidOut_resignationTypeBuyBackAndPaidOutTrue_noErrorIsAddedToForm(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            paid_out=True,
        )
        form = MembershipResignationForm(
            data={
                "share_owner": ShareOwnerFactory.create(),
                "cancellation_date": resignation.cancellation_date,
                "cancellation_reason": resignation.cancellation_reason,
                "resignation_type": resignation.resignation_type,
                "paid_out": resignation.paid_out,
            }
        )
        self.assertNotIn("paid_out", form.errors.keys())

    def test_validateSetMemberStatusInvesting_noOptionSelected_errorAddedToForm(
        self,
    ):
        form = MembershipResignationForm(
            data={
                "share_owner": ShareOwnerFactory.create(),
                "resignation_type": MembershipResignation.ResignationType.BUY_BACK,
                "set_member_status_investing": MembershipResignationForm.SetMemberStatusInvestingChoices.NOT_SELECTED,
            }
        )
        self.assertIn("set_member_status_investing", form.errors.keys())

    def test_validateSetMemberStatusInvesting_optionSelected_noErrorAddedToForm(
        self,
    ):
        form = MembershipResignationForm(
            data={
                "share_owner": ShareOwnerFactory.create(),
                "resignation_type": MembershipResignation.ResignationType.BUY_BACK,
                "set_member_status_investing": MembershipResignationForm.SetMemberStatusInvestingChoices.MEMBER_BECOMES_INVESTING,
            }
        )
        self.assertNotIn("set_member_status_investing", form.errors.keys())

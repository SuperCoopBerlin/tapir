import datetime
from http import HTTPStatus
from unittest.mock import patch, Mock

from django.core import mail
from django.urls import reverse

from tapir import settings
from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.emails.membershipresignation_confirmation_email import (
    MembershipResignationConfirmation,
)
from tapir.coop.emails.membershipresignation_transferred_shares_confirmation import (
    MembershipResignationTransferredSharesConfirmation,
)
from tapir.coop.forms import MembershipResignationForm
from tapir.coop.models import (
    MembershipResignation,
    MembershipResignationCreateLogEntry,
    ShareOwner,
    UpdateShareOwnerLogEntry,
)
from tapir.coop.services.membership_resignation_service import (
    MembershipResignationService,
)
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
    TapirEmailTestMixin,
    PermissionTestMixin,
)


class TestMembershipResignationCreateView(
    PermissionTestMixin, FeatureFlagTestMixin, TapirEmailTestMixin, TapirFactoryTestBase
):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
            settings.GROUP_MEMBER_OFFICE,
        ]

    def do_request(self):
        return self.client.get(reverse("coop:membership_resignation_create"))

    def test_membershipResignationCreateView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_vorstand()
        response = self.client.get(reverse("coop:membership_resignation_create"))
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    def call_resignation_create_view(
        self,
        resignation_type: MembershipResignation.ResignationType,
        transferring_shares_to: ShareOwner | None = None,
    ):
        resigning_member = ShareOwnerFactory.create()
        data = {
            "share_owner": resigning_member.id,
            "cancellation_reason": "Test resignation",
            "cancellation_reason_category": MembershipResignation.CancellationReasons.OTHER,
            "cancellation_date": self.TODAY,
            "resignation_type": resignation_type,
        }
        if transferring_shares_to:
            data["transferring_shares_to"] = transferring_shares_to.id

        response = self.client.post(
            reverse("coop:membership_resignation_create"),
            data=data,
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)
        return MembershipResignation.objects.get()

    @patch.object(MembershipResignationService, "update_membership_pauses")
    @patch.object(
        MembershipResignationService, "update_shifts_and_shares_and_pay_out_day"
    )
    def test_membershipResignationCreateView_default_changesApplied(
        self,
        mock_update_shifts_and_shares_and_pay_out_day: Mock,
        mock_delete_shareowner_membershippauses: Mock,
    ):
        actor = self.login_as_vorstand()
        resignation = self.call_resignation_create_view(
            MembershipResignation.ResignationType.GIFT_TO_COOP
        )
        self.assertEqual(1, MembershipResignation.objects.count())
        mock_delete_shareowner_membershippauses.assert_called_once_with(resignation)
        mock_update_shifts_and_shares_and_pay_out_day.assert_called_once_with(
            resignation=resignation, actor=actor
        )

    def test_membershipResignationCreateView_default_logEntryCreated(self):
        actor = self.login_as_vorstand()
        self.call_resignation_create_view(
            MembershipResignation.ResignationType.GIFT_TO_COOP
        )

        self.assertEqual(1, MembershipResignationCreateLogEntry.objects.count())
        log_entry = MembershipResignationCreateLogEntry.objects.get()
        created_resignation = MembershipResignation.objects.get()
        self.assertEqual(created_resignation.id, int(log_entry.values["id"]))
        self.assertEqual(actor, log_entry.actor)

    def test_membershipResignationCreateView_default_correctMailSent(self):
        self.login_as_vorstand()
        member_to_resign = self.call_resignation_create_view(
            MembershipResignation.ResignationType.GIFT_TO_COOP
        )

        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            MembershipResignationConfirmation,
            member_to_resign.share_owner.email,
            sent_mail,
        )

    def test_membershipResignationCreateView_resignationTypeTransfer_shareRecipientAlsoReceivesMails(
        self,
    ):
        member_that_receives_shares = ShareOwnerFactory.create()
        self.login_as_vorstand()
        resignation = self.call_resignation_create_view(
            MembershipResignation.ResignationType.TRANSFER,
            member_that_receives_shares,
        )
        member_that_gifts_shares = resignation.share_owner

        self.assertEqual(2, len(mail.outbox))
        mail_to_resigned_member = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            MembershipResignationConfirmation,
            member_that_gifts_shares.email,
            mail_to_resigned_member,
        )
        mail_to_receiving_member = mail.outbox[1]
        self.assertEmailOfClass_GotSentTo(
            MembershipResignationTransferredSharesConfirmation,
            member_that_receives_shares.email,
            mail_to_receiving_member,
        )

    def test_membershipResignationCreateView_resignationTypeGiftToCoop_payOutDayIsSetCorrectly(
        self,
    ):
        self.login_as_vorstand()
        member_to_resign = self.call_resignation_create_view(
            MembershipResignation.ResignationType.GIFT_TO_COOP
        )

        self.assertEqual(self.TODAY, member_to_resign.pay_out_day)

    def test_membershipResignationCreateView_resignationTypeBuyBack_payOutDayIsSetCorrectly(
        self,
    ):
        self.login_as_vorstand()
        resignation = self.call_resignation_create_view(
            MembershipResignation.ResignationType.BUY_BACK
        )
        self.assertEqual(
            datetime.date(year=2027, month=12, day=31),
            resignation.pay_out_day,
        )

    def test_membershipResignationCreateView_memberStaysActive_memberStillActive(
        self,
    ):
        self.login_as_vorstand()
        resigning_member = ShareOwnerFactory.create(is_investing=False)
        data = {
            "share_owner": resigning_member.id,
            "cancellation_reason": "Test resignation",
            "cancellation_date": self.TODAY,
            "resignation_type": MembershipResignation.ResignationType.BUY_BACK,
            "set_member_status_investing": MembershipResignationForm.SetMemberStatusInvestingChoices.MEMBER_STAYS_ACTIVE,
        }

        response = self.client.post(
            reverse("coop:membership_resignation_create"),
            data=data,
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)

        resigning_member.refresh_from_db()
        self.assertFalse(resigning_member.is_investing)

    def test_membershipResignationCreateView_memberToInvesting_memberIsInvestingAndLogEntryCreated(
        self,
    ):
        self.login_as_vorstand()
        resigning_member = ShareOwnerFactory.create(is_investing=False)
        data = {
            "share_owner": resigning_member.id,
            "cancellation_reason": "Test resignation",
            "cancellation_reason_category": MembershipResignation.CancellationReasons.OTHER,
            "cancellation_date": self.TODAY,
            "resignation_type": MembershipResignation.ResignationType.BUY_BACK,
            "set_member_status_investing": MembershipResignationForm.SetMemberStatusInvestingChoices.MEMBER_BECOMES_INVESTING,
        }

        response = self.client.post(
            reverse("coop:membership_resignation_create"),
            data=data,
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)

        resigning_member.refresh_from_db()
        self.assertTrue(resigning_member.is_investing)
        self.assertEqual(1, UpdateShareOwnerLogEntry.objects.count())

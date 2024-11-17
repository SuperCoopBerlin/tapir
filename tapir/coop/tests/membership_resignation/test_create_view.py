import datetime
from http import HTTPStatus
from unittest.mock import patch, Mock
from icecream import ic

from django.core import mail
from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.emails.membershipresignation_confirmation_email import (
    MembershipResignationConfirmation,
)
from tapir.coop.emails.membershipresignation_transferred_shares_confirmation import (
    MembershipResignationTransferredSharesConfirmation,
)
from tapir.coop.models import (
    MembershipResignation,
    MembershipResignationCreateLogEntry,
    TapirUser,
)
from tapir.coop.services.MembershipResignationService import (
    MembershipResignationService,
)
from tapir.coop.tests.factories import ShareOwnerFactory, MembershipResignationFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
    TapirEmailTestMixin,
)


class TestMembershipResignationCreateView(
    FeatureFlagTestMixin, TapirEmailTestMixin, TapirFactoryTestBase
):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_membershipResignationCreateView_loggedInAsNormalUser_accessDenied(self):
        self.login_as_normal_user()
        response = self.client.get(reverse("coop:resign_new_membership"))
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    def test_membershipResignationCreateView_loggedInAsMemberOffice_accessGranted(self):
        self.login_as_member_office_user()
        response = self.client.get(reverse("coop:resign_new_membership"))
        self.assertStatusCode(response, HTTPStatus.OK)

    def test_membershipResignationCreateView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_member_office_user()
        response = self.client.get(reverse("coop:resign_new_membership"))
        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    def create_default_resignation(self):
        share_owner = ShareOwnerFactory.create()
        actor = self.login_as_member_office_user()
        response = self.client.post(
            reverse("coop:resign_new_membership"),
            data={
                "share_owner": share_owner.id,
                "cancellation_reason": "Test resignation",
                "cancellation_date": self.TODAY,
                "resignation_type": MembershipResignation.ResignationType.GIFT_TO_COOP,
            },
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)
        resignation = MembershipResignation.objects.last()
        return resignation, actor

    @patch.object(MembershipResignationService, "delete_shareowner_membershippauses")
    @patch.object(
        MembershipResignationService, "update_shifts_and_shares_and_pay_out_day"
    )
    def test_membershipResignationCreateView_default_changesApplied(
        self,
        mock_delete_shareowner_membershippauses: Mock,
        mock_update_shifts_and_shares_and_pay_out_day: Mock,
    ):
        resignation = self.create_default_resignation()
        self.assertEqual(1, MembershipResignation.objects.count())
        mock_delete_shareowner_membershippauses.assert_called_once_with(
            resignation=resignation
        )
        mock_update_shifts_and_shares_and_pay_out_day.assert_called_once_with(
            resignation=resignation
        )

    def test_membershipResignationCreateView_default_logEntryCreated(self):
        _, actor = self.create_default_resignation()

        self.assertEqual(1, MembershipResignationCreateLogEntry.objects.count())
        log_entry = MembershipResignationCreateLogEntry.objects.get()
        created_resignation = MembershipResignation.objects.get()
        self.assertEqual(created_resignation.id, int(log_entry.values["id"]))
        self.assertEqual(actor, log_entry.actor)

    def test_membershipResignationCreateView_default_correctMailSent(self):
        member_to_resign, _ = self.create_default_resignation()

        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            MembershipResignationConfirmation,
            member_to_resign.share_owner.email,
            sent_mail,
        )

    def test_membershipResignationCreateView_sharesTransferred_shareRecipientAlsoReceivesMails(
        self,
    ):
        member_to_resign = ShareOwnerFactory.create()
        member_that_receives_shares = ShareOwnerFactory.create()
        self.login_as_member_office_user()
        response = self.client.post(
            reverse("coop:resign_new_membership"),
            data={
                "share_owner": member_to_resign.id,
                "cancellation_reason": "Test resignation",
                "cancellation_date": self.TODAY,
                "resignation_type": MembershipResignation.ResignationType.TRANSFER,
                "transferring_shares_to": member_that_receives_shares.id,
            },
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)

        self.assertEqual(2, len(mail.outbox))
        mail_to_resigned_member = mail.outbox[0]
        self.assertEmailOfClass_GotSentTo(
            MembershipResignationConfirmation,
            member_to_resign.email,
            mail_to_resigned_member,
        )
        mail_to_receiving_member = mail.outbox[1]
        self.assertEmailOfClass_GotSentTo(
            MembershipResignationTransferredSharesConfirmation,
            member_that_receives_shares.email,
            mail_to_receiving_member,
        )

    def test_membershipResignationCreateView_default_payOutDayIsSetCorrectly(self):
        member_to_resign, _ = self.create_default_resignation()

        self.assertEqual(self.TODAY, member_to_resign.pay_out_day)

    def test_membershipResignationCreateView_resignationTypeBuyBack_payOutDayIsSetCorrectly(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create()
        response = self.client.post(
            reverse("coop:resign_new_membership"),
            data={
                "share_owner": share_owner.id,
                "cancellation_reason": "Test resignation",
                "cancellation_date": self.TODAY,
                "resignation_type": MembershipResignation.ResignationType.BUY_BACK,
            },
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)
        member_to_resign = MembershipResignation.objects.last()
        self.assertEqual(
            datetime.date(year=2027, month=12, day=31),
            member_to_resign.pay_out_day,
        )

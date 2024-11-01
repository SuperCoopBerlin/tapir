import datetime
from http import HTTPStatus
from icecream import ic

from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import MembershipResignationUpdateLogEntry, MembershipResignation
from tapir.coop.tests.factories import MembershipResignationFactory, ShareOwnerFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestMembershipResignationEditView(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    # def test_membershipResignationEditView_loggedInAsNormalUser_accessDenied(self):
    #     self.login_as_normal_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.get(
    #         reverse("coop:resign_member_edit", args=[resignation.id])
    #     )

    #     self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    # def test_membershipResignationEditView_loggedInAsMemberOffice_accessGranted(self):
    #     self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.get(
    #         reverse("coop:resign_member_edit", args=[resignation.id])
    #     )

    #     self.assertStatusCode(response, HTTPStatus.OK)

    # def test_membershipResignationEditView_featureFlagDisabled_accessDenied(self):
    #     self.given_feature_flag_value(feature_flag_membership_resignation, False)
    #     self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.get(
    #         reverse("coop:resign_member_edit", args=[resignation.id])
    #     )

    #     self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    # def test_membershipResignationEditView_default_logEntryCreated(self):
    #     actor = self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.post(
    #         reverse("coop:resign_member_edit", args=[resignation.id]),
    #         data={
    #             "cancellation_reason": "Reason after edit",
    #             "cancellation_date": self.TODAY,
    #         },
    #     )
    #     self.assertStatusCode(response, HTTPStatus.OK)

    #     self.assertEqual(1, MembershipResignationUpdateLogEntry.objects.count())
    #     log_entry = MembershipResignationUpdateLogEntry.objects.get()
    #     created_resignation = MembershipResignation.objects.get()
    #     self.assertEqual(created_resignation.id, int(log_entry.values["id"]))
    #     self.assertEqual(actor, log_entry.actor)

    # def test_membershipResignationEditView_default_cantChangeBaseFields(self):
    #     self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create(
    #         resignation_type=MembershipResignation.ResignationType.GIFT_TO_COOP
    #     )
    #     old_resigned_member = resignation.share_owner
    #     new_resigned_member = ShareOwnerFactory.create()
    #     new_recipient = ShareOwnerFactory.create()

    #     response = self.client.post(
    #         reverse("coop:resign_member_edit", args=[resignation.id]),
    #         data={
    #             "share_owner": new_resigned_member.id,
    #             "transferring_shares_to": new_recipient.id,
    #             "resignation_type": MembershipResignation.ResignationType.TRANSFER,
    #         },
    #     )
    #     self.assertStatusCode(response, HTTPStatus.OK)

    #     resignation.refresh_from_db()
    #     self.assertEqual(old_resigned_member, resignation.share_owner)
    #     self.assertEqual(None, resignation.transferring_shares_to)
    #     self.assertEqual(
    #         MembershipResignation.ResignationType.GIFT_TO_COOP,
    #         resignation.resignation_type,
    #     )

    def test_membershipResignationEditView_cancellationDateUpdate_payOutDayUpdated(
        self,
    ):
        self.login_as_member_office_user()
        resignation: MembershipResignation = MembershipResignationFactory.create(
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=2020, month=6, day=20),
        )
        self.assertEqual(
            datetime.date(year=2023, month=12, day=31), resignation.pay_out_day
        )
        response = self.client.post(
            reverse("coop:resign_member_edit", args=[resignation.id]),
            data={
                "share_owner": resignation.share_owner.id,
                "cancellation_reason": resignation.cancellation_reason,
                "cancellation_date": datetime.date(year=2022, month=7, day=30),
                "pay_out_day": resignation.pay_out_day,
                "resignation_type": MembershipResignation.ResignationType.TRANSFER,
                "paid_out": False,
                "transferring_shares_to": ShareOwnerFactory.create().id,
            },
        )
        self.assertStatusCode(response, HTTPStatus.FOUND)
        resignation.refresh_from_db()
        self.assertEqual(
            datetime.date(year=2025, month=12, day=31),
            resignation.pay_out_day,
        )

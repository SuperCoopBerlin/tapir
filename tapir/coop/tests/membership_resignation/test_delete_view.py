import datetime
from http import HTTPStatus
from icecream import ic
import json

from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import (
    MembershipResignation,
    MembershipResignationUpdateLogEntry,
    ShareOwnership,
)
from tapir.coop.tests.factories import (
    MembershipResignationFactory,
    ShareOwnershipFactory,
    ShareOwnerFactory,
)
from tapir.utils.tests_utils import FeatureFlagTestMixin, TapirFactoryTestBase


class TestMembershipResignationDeleteView(FeatureFlagTestMixin, TapirFactoryTestBase):
    def setUp(self) -> None:
        super().setUp()

    # def test_membershipResignationDeleteView_loggedInAsNormalUser_accessDenied(self):
    #     self.given_feature_flag_value(feature_flag_membership_resignation, True)
    #     self.login_as_normal_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.post(
    #         reverse("coop:resign_member_remove", args=[resignation.id]),
    #         data=resignation.data,
    #         follow=True,
    #     )

    #     self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    # def test_membershipResignationDeleteView_loggedInAsMemberOffice_accessGranted(self):
    #     self.given_feature_flag_value(feature_flag_membership_resignation, True)
    #     self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.post(
    #         reverse("coop:resign_member_remove", args=[resignation.id]),
    #         data=resignation.data,
    #         follow=True,
    #     )

    #     self.assertStatusCode(response, HTTPStatus.FOUND)

    # def test_membershipResignationDeleteView_featureFlagDisabled_accessDenied(self):
    #     self.given_feature_flag_value(feature_flag_membership_resignation, False)
    #     self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()

    #     response = self.client.post(
    #         reverse("coop:resign_member_remove", args=[resignation.id]),
    #         follow=True,
    #     )

    #     self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    # def test_membershipResignationDeleteView_default_sharesEndDateSetToNone(self):
    #     self.given_feature_flag_value(feature_flag_membership_resignation, True)
    #     self.login_as_member_office_user()
    #     resignation: MembershipResignation = MembershipResignationFactory.create()
    #     resignation.share_owner.share_ownerships.update(end_date=datetime.date.today())

    #     response = self.client.post(
    #         reverse("coop:resign_member_remove", args=[resignation.id]),
    #         data=resignation.data,
    #         follow=True,
    #     )

    #     self.assertStatusCode(response, HTTPStatus.OK)
    #     self.assertTrue(
    #         all(
    #             [
    #                 share_ownership.end_date is None
    #                 for share_ownership in resignation.share_owner.share_ownerships.all()
    #             ]
    #         )
    #     )

    def test_membershipResignationDeleteView_default_logEntryCreated(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        actor = self.login_as_member_office_user()
        resignation: MembershipResignation = MembershipResignationFactory.create()
        ShareOwnershipFactory.create(share_owner=resignation.share_owner)

        response = self.client.post(
            reverse("coop:resign_member_remove", args=[resignation.id]),
            follow=True,
        )
        self.assertEqual(MembershipResignation.objects.all().count(), 0)
        for shareownership in ShareOwnership.objects.filter(
            share_owner=resignation.share_owner
        ):
            self.assertEqual(shareownership.end_date, None)
        ic(response)
        self.assertRedirects(response, reverse("coop:resigned_members_list"))
        self.assertEqual(1, MembershipResignationUpdateLogEntry.objects.count())
        log_entry = MembershipResignationUpdateLogEntry.objects.get()
        created_resignation = MembershipResignation.objects.get()
        self.assertEqual(created_resignation.id, int(log_entry.values["id"]))
        self.assertEqual(actor, log_entry.actor)

        self.fail(
            "No corresponding log entry class, see "
            "TestMembershipResignationEditView.test_membershipResignationEditView_default_logEntryCreated "
            "for an example on how to test log entries"
        )

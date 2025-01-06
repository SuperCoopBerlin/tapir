import datetime
from http import HTTPStatus
from unittest.mock import patch, Mock

from django.urls import reverse
from django.utils import timezone

from tapir import settings
from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import (
    MembershipResignation,
    MembershipResignationDeleteLogEntry,
)
from tapir.coop.services.membership_resignation_service import (
    MembershipResignationService,
)
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.coop.tests.factories import (
    MembershipResignationFactory,
    ShareOwnerFactory,
)
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    PermissionTestMixin,
)


class TestMembershipResignationDeleteView(
    PermissionTestMixin, FeatureFlagTestMixin, TapirFactoryTestBase
):
    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)

    def permission_test_get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
            settings.GROUP_MEMBER_OFFICE,
        ]

    def permission_test_do_request(self):
        resignation: MembershipResignation = MembershipResignationFactory.create()
        return self.client.post(
            reverse("coop:membership_resignation_delete", args=[resignation.id]),
            follow=True,
        )

    def test_membershipResignationDeleteView_featureFlagDisabled_accessDenied(self):
        self.given_feature_flag_value(feature_flag_membership_resignation, False)
        self.login_as_vorstand()
        resignation: MembershipResignation = MembershipResignationFactory.create()

        response = self.client.post(
            reverse("coop:membership_resignation_delete", args=[resignation.id]),
        )

        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    @patch.object(MembershipResignationService, "on_resignation_deleted")
    def test_membershipResignationDeleteView_default_sharesEndDateSetToNone(
        self, mock_on_resignation_deleted: Mock
    ):
        self.login_as_vorstand()
        resignation: MembershipResignation = MembershipResignationFactory.create()
        resignation.share_owner.share_ownerships.update(end_date=datetime.date.today())

        response = self.client.post(
            reverse("coop:membership_resignation_delete", args=[resignation.id]),
            follow=True,
        )

        self.assertStatusCode(response, HTTPStatus.OK)
        mock_on_resignation_deleted.assert_called_once_with(resignation)

    def test_membershipResignationDeleteView_default_logEntryCreated(self):
        actor = self.login_as_vorstand()
        resignation: MembershipResignation = MembershipResignationFactory.create()
        response = self.client.post(
            reverse("coop:membership_resignation_delete", args=[resignation.id]),
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)
        self.assertEqual(MembershipResignation.objects.all().count(), 0)
        self.assertEqual(MembershipResignationDeleteLogEntry.objects.count(), 1)
        log_entry = MembershipResignationDeleteLogEntry.objects.get()
        self.assertEqual(resignation.id, int(log_entry.values["id"]))
        self.assertEqual(actor, log_entry.actor)

    def test_membershipResignationDeleteView_sharesWereTransferred_updateTransferredShares(
        self,
    ):
        self.login_as_vorstand()
        member_that_gifts_shares = ShareOwnerFactory.create(nb_shares=3)
        member_that_receives_shares = ShareOwnerFactory.create(nb_shares=1)
        cancellation_date = timezone.now().date()

        data = {
            "share_owner": member_that_gifts_shares.id,
            "cancellation_reason": "Test resignation",
            "cancellation_reason_category": MembershipResignation.CancellationReasons.OTHER,
            "cancellation_date": cancellation_date,
            "resignation_type": MembershipResignation.ResignationType.TRANSFER,
            "transferring_shares_to": member_that_receives_shares.id,
        }

        response = self.client.post(
            reverse("coop:membership_resignation_create"),
            data=data,
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)

        self.assertNumberOfSharesAtDate(
            member_that_receives_shares, 1, cancellation_date
        )
        self.assertNumberOfSharesAtDate(member_that_gifts_shares, 3, cancellation_date)
        new_shares_date = cancellation_date + datetime.timedelta(days=1)
        self.assertNumberOfSharesAtDate(member_that_receives_shares, 4, new_shares_date)
        self.assertNumberOfSharesAtDate(member_that_gifts_shares, 0, new_shares_date)

        resignation = MembershipResignation.objects.get()
        response = self.client.post(
            reverse("coop:membership_resignation_delete", args=[resignation.id]),
            follow=True,
        )
        self.assertStatusCode(response, HTTPStatus.OK)

        self.assertNumberOfSharesAtDate(
            member_that_receives_shares, 1, cancellation_date
        )
        self.assertNumberOfSharesAtDate(member_that_gifts_shares, 3, cancellation_date)
        self.assertNumberOfSharesAtDate(member_that_receives_shares, 1, new_shares_date)
        self.assertNumberOfSharesAtDate(member_that_gifts_shares, 3, new_shares_date)

    def assertNumberOfSharesAtDate(self, member, number_of_shares, date):
        self.assertEqual(
            number_of_shares,
            NumberOfSharesService.get_number_of_active_shares(member, date),
        )

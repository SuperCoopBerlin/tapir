import datetime
from http import HTTPStatus
from unittest.mock import patch, Mock

from django.urls import reverse

from tapir import settings
from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import (
    MembershipResignation,
    MembershipResignationDeleteLogEntry,
)
from tapir.coop.services.MembershipResignationService import (
    MembershipResignationService,
)
from tapir.coop.tests.factories import (
    MembershipResignationFactory,
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

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
        ]

    def do_request(self):
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

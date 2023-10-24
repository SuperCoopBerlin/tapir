import datetime

from django.urls import reverse

from tapir.coop.models import (
    MembershipPauseCreatedLogEntry,
    MembershipPause,
    MembershipPauseUpdatedLogEntry,
)
from tapir.coop.tests.factories import ShareOwnerFactory, MembershipPauseFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestRegisterDraftUser(TapirFactoryTestBase):
    def test_createPause_default_logCreated(self):
        self.login_as_member_office_user()
        self.assertEqual(0, MembershipPauseCreatedLogEntry.objects.count())
        self.assertEqual(0, MembershipPause.objects.count())

        response = self.client.post(
            reverse("coop:membership_pause_create"),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "test description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, MembershipPause.objects.count())
        self.assertEqual(1, MembershipPauseCreatedLogEntry.objects.count())

    def test_createPause_loggedInAsNormalMember_returns403(self):
        self.login_as_normal_user()

        response = self.client.post(
            reverse("coop:membership_pause_create"),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "test description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(0, MembershipPauseCreatedLogEntry.objects.count())
        self.assertEqual(0, MembershipPause.objects.count())

    def test_editPause_default_logCreated(self):
        self.login_as_member_office_user()
        pause = MembershipPauseFactory.create(description="Start description")
        self.assertEqual(0, MembershipPauseUpdatedLogEntry.objects.count())

        response = self.client.post(
            reverse("coop:membership_pause_edit", args=[pause.id]),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "End description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, MembershipPauseUpdatedLogEntry.objects.count())
        pause.refresh_from_db()
        self.assertEqual(pause.description, "End description")

    def test_editPause_loggedInAsNormalMember_returns403(self):
        self.login_as_normal_user()
        pause = MembershipPauseFactory.create(description="Test description")

        response = self.client.post(
            reverse("coop:membership_pause_edit", args=[pause.id]),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "rejected description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(0, MembershipPauseUpdatedLogEntry.objects.count())
        self.assertEqual("Test description", pause.description)

    def test_pauseList_viewerIsInMemberOffice_canSeeAllPauses(self):
        logged_in_user = self.login_as_member_office_user()
        pauses = {
            MembershipPauseFactory.create(share_owner=logged_in_user.share_owner),
            MembershipPauseFactory.create(),
        }

        response = self.client.get(reverse("coop:membership_pauses"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(set(response.context["object_list"]), pauses)

    def test_pauseList_viewerIsNotMemberOffice_canOnlySeeOwnPauses(self):
        logged_in_user = self.login_as_normal_user()
        pause_of_logged_in_user = MembershipPauseFactory.create(
            share_owner=logged_in_user.share_owner
        )
        MembershipPauseFactory.create()  # pause of another member

        response = self.client.get(reverse("coop:membership_pauses"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            set(response.context["object_list"]), {pause_of_logged_in_user}
        )

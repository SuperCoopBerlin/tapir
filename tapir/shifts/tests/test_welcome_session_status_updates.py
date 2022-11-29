import datetime

from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import ShiftAccountEntry
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestWelcomeSessionStatusUpdates(TapirFactoryTestBase):
    MESSAGE_START_WITHOUT_ENTRY = (
        "The test assumes that the user starts without any account entry"
    )
    VIEW_NAME_SHAREOWNER_UPDATE = "coop:shareowner_update"

    def test_on_welcome_session_marked_as_attended(self):
        self.login_as_member_office_user()
        tapir_user: TapirUser = TapirUserFactory.create(
            share_owner__attended_welcome_session=False
        )

        self.assertFalse(
            ShiftAccountEntry.objects.filter(user=tapir_user).exists(),
            self.MESSAGE_START_WITHOUT_ENTRY,
        )
        self.client.post(
            reverse(
                "coop:mark_shareowner_attended_welcome_session",
                args=[tapir_user.share_owner.id],
            )
        )
        self.assertEqual(
            tapir_user.shift_user_data.get_account_balance(),
            1,
            "Attending a welcome session should count as a shift, the member should have an balance of 1",
        )
        self.assertTrue(
            ShiftAccountEntry.objects.filter(user=tapir_user)
            .first()
            .is_from_welcome_session,
            "The created account entry should have the 'is_from_welcome_session' set to true",
        )

    def test_share_owner_update_view_session_attended(self):
        self.login_as_member_office_user()
        tapir_user: TapirUser = TapirUserFactory.create(
            share_owner__attended_welcome_session=False
        )

        tapir_user.share_owner.blank_info_fields()
        tapir_user.share_owner.save()

        self.assertFalse(
            ShiftAccountEntry.objects.filter(user=tapir_user).exists(),
            self.MESSAGE_START_WITHOUT_ENTRY,
        )

        response = self.client.post(
            path=reverse(
                self.VIEW_NAME_SHAREOWNER_UPDATE,
                args=[tapir_user.share_owner.id],
            ),
            data={"attended_welcome_session": True},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            tapir_user.shift_user_data.get_account_balance(),
            1,
            "Attending a welcome session should count as a shift, the member should have an balance of 1",
        )
        self.assertTrue(
            ShiftAccountEntry.objects.filter(user=tapir_user)
            .first()
            .is_from_welcome_session,
            "The created account entry should have the 'is_from_welcome_session' set to true",
        )

    def test_share_owner_update_view_session_attended_account_entry_already_exists(
        self,
    ):
        self.login_as_member_office_user()
        tapir_user: TapirUser = TapirUserFactory.create(
            share_owner__attended_welcome_session=False
        )

        tapir_user.share_owner.blank_info_fields()
        tapir_user.share_owner.save()

        self.assertFalse(
            ShiftAccountEntry.objects.filter(user=tapir_user).exists(),
            self.MESSAGE_START_WITHOUT_ENTRY,
        )

        ShiftAccountEntry.objects.create(
            is_from_welcome_session=True,
            user=tapir_user,
            description="Welcome session / Willkommenstreffen",
            date=datetime.date.today(),
            value=1,
        )

        response = self.client.post(
            path=reverse(
                self.VIEW_NAME_SHAREOWNER_UPDATE,
                args=[tapir_user.share_owner.id],
            ),
            data={"attended_welcome_session": True},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            ShiftAccountEntry.objects.filter(user=tapir_user).count(),
            1,
            "No new entry should have been created",
        )

    def test_share_owner_update_view_session_not_attended(self):
        self.login_as_member_office_user()
        tapir_user: TapirUser = TapirUserFactory.create(
            share_owner__attended_welcome_session=True
        )

        ShiftAccountEntry.objects.create(
            is_from_welcome_session=True,
            user=tapir_user,
            description="Welcome session / Willkommenstreffen",
            date=datetime.date.today(),
            value=1,
        )

        tapir_user.share_owner.blank_info_fields()
        tapir_user.share_owner.save()

        response = self.client.post(
            path=reverse(
                self.VIEW_NAME_SHAREOWNER_UPDATE,
                args=[tapir_user.share_owner.id],
            ),
            data={"attended_welcome_session": False},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            tapir_user.shift_user_data.get_account_balance(),
            0,
            "Since the welcome session attendance got cancelled, the account entry should have been removed",
        )
        self.assertFalse(
            ShiftAccountEntry.objects.filter(user=tapir_user).exists(),
            "Since the welcome session attendance got cancelled, the account entry should have been removed",
        )

    def test_on_tapir_account_creation_welcome_session_attended(self):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(attended_welcome_session=True)

        response = self.client.post(
            reverse("coop:create_user_from_shareowner", args=[share_owner.id]),
            data={"username": "test.user"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        tapir_user = TapirUser.objects.get(share_owner=share_owner)
        self.assertEqual(
            tapir_user.shift_user_data.get_account_balance(),
            1,
            "Since the member has attended the welcome session, they should have a balance of 1 on account creation",
        )

    def test_on_tapir_account_creation_welcome_session_not_attended(self):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(attended_welcome_session=False)

        response = self.client.post(
            reverse("coop:create_user_from_shareowner", args=[share_owner.id]),
            data={"username": "test.user"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        tapir_user = TapirUser.objects.get(share_owner=share_owner)
        self.assertEqual(
            tapir_user.shift_user_data.get_account_balance(),
            0,
            "Since the member hasn't attended the welcome session, they should have a balance of 0 on account creation",
        )

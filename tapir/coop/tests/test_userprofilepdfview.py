from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import ShiftAccountEntry, ShiftAttendance
from tapir.shifts.tests.factories import (
    ShiftFactory,
    ShiftSlotFactory,
)
from tapir.utils.tests_utils import PermissionTestMixin, TapirFactoryTestBase


class TestUserProfilePDFView(PermissionTestMixin, TapirFactoryTestBase):

    def setUp(self):
        super().setUp()
        self.tapir_user = TapirUserFactory.create()
        self.url = reverse(
            "coop:user_profile_pdf", args=[self.tapir_user.share_owner.id]
        )

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_MEMBER_OFFICE,
            settings.GROUP_EMPLOYEES,
        ]

    def do_request(self):
        return self.client.get(self.url)

    def test_userProfilePDFView_loggedInAsMemberOffice_returnsPDFContentType(self):
        self.login_as_member_office_user()
        response = self.client.get(self.url)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_userProfilePDFView_loggedInAsMemberOffice_correctFilenameInHeader(self):
        self.login_as_member_office_user()
        response = self.client.get(self.url)
        expected_filename = f"user-{self.tapir_user.share_owner.id}-profile.pdf"
        self.assertIn(
            expected_filename,
            response["Content-Disposition"],
        )

    def test_userProfilePDFView_shareOwnerWithoutUser_attendancesEmpty(self):
        self.login_as_member_office_user()
        shareowner_without_user = ShareOwnerFactory.create()
        url = reverse("coop:user_profile_pdf", args=[shareowner_without_user.pk])
        response = self.client.get(url)

        self.assertEqual(response.context["attendances"], [])

    def test_userProfilePDFView_recentShifts_attendancesIncluded(self):
        shift = ShiftFactory.create(start_time=timezone.now() - timedelta(days=10))
        slot = ShiftSlotFactory.create(shift=shift)
        ShiftAttendance.objects.create(slot=slot, user=self.tapir_user)

        self.login_as_member_office_user()
        response = self.client.get(self.url)

        attendances = response.context["attendances"]
        self.assertEqual(len(attendances), 1)
        self.assertEqual(attendances[0].user, self.tapir_user)

    def test_userProfilePDFView_oldShifts_attendancesExcluded(self):
        cutoff = timezone.now() - relativedelta(years=settings.SHIFT_RETENTION_YEARS)
        old_shift = ShiftFactory.create(start_time=cutoff - timedelta(days=1))
        old_slot = ShiftSlotFactory.create(shift=old_shift)
        ShiftAttendance.objects.create(user=self.tapir_user, slot=old_slot)

        self.login_as_member_office_user()
        response = self.client.get(self.url)

        attendances = response.context["attendances"]
        self.assertEqual(len(attendances), 0)

    def test_userProfilePDFView_recentEntries_entriesDataIncluded(self):
        entry_date = timezone.now() - timedelta(days=5)
        ShiftAccountEntry.objects.create(user=self.tapir_user, date=entry_date, value=1)

        self.login_as_member_office_user()
        response = self.client.get(self.url)

        entries_data = response.context["entries_data"]
        self.assertEqual(len(entries_data), 1)
        self.assertIn("entry", entries_data[0])
        self.assertIn("balance_at_date", entries_data[0])

    def test_userProfilePDFView_accountEntry_balanceCalculatedAtEntryDate(self):
        entry_date = timezone.now() - timedelta(days=5)
        ShiftAccountEntry.objects.create(user=self.tapir_user, date=entry_date, value=1)

        self.login_as_member_office_user()
        response = self.client.get(self.url)

        entries_data = response.context["entries_data"]
        self.assertEqual(len(entries_data), 1)
        balance = entries_data[0]["balance_at_date"]
        self.assertIsNotNone(balance)

    def test_userProfilePDFView_nonexistentShareOwner_returns404(self):
        self.login_as_member_office_user()
        url = reverse("coop:user_profile_pdf", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_userProfilePDFView_loggedInAsMemberOffice_pdfGenerationSucceeds(self):
        self.login_as_member_office_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)

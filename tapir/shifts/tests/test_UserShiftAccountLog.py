import datetime

from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAccountEntry
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestUserShiftAccountLog(TapirFactoryTestBase):
    VIEW_NAME = "shifts:user_shift_account_log"

    def test_userShiftAccountLog_loggedInAsNormalUser_canSeeOwnLog(self):
        tapir_user = self.login_as_normal_user()

        response = self.client.get(reverse(self.VIEW_NAME, args=[tapir_user.id]))

        self.assertEqual(200, response.status_code)

    def test_userShiftAccountLog_loggedInAsNormalUser_cannotSeeLogOfOtherUser(self):
        self.login_as_normal_user()
        other_tapir_user = TapirUserFactory.create()

        response = self.client.get(reverse(self.VIEW_NAME, args=[other_tapir_user.id]))

        self.assertEqual(403, response.status_code)

    def test_userShiftAccountLog_loggedInAsMemberOffice_canSeeLogOfOtherUser(self):
        self.login_as_member_office_user()
        other_tapir_user = TapirUserFactory.create()

        response = self.client.get(reverse(self.VIEW_NAME, args=[other_tapir_user.id]))

        self.assertEqual(200, response.status_code)

    def test_userShiftAccountLog_default_contextDateIsCorrect(self):
        self.login_as_member_office_user()
        other_tapir_user = TapirUserFactory.create()
        entries = ShiftAccountEntry.objects.bulk_create(
            [
                ShiftAccountEntry(
                    user=other_tapir_user,
                    value=-3,
                    date=datetime.date(year=2024, month=1, day=1),
                ),
                ShiftAccountEntry(
                    user=other_tapir_user,
                    value=2,
                    date=datetime.date(year=2024, month=2, day=1),
                ),
                ShiftAccountEntry(
                    user=other_tapir_user,
                    value=-1,
                    date=datetime.date(year=2024, month=3, day=1),
                ),
            ]
        )

        response: TemplateResponse = self.client.get(
            reverse(self.VIEW_NAME, args=[other_tapir_user.id])
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(other_tapir_user, response.context_data["user"])

        self.assertEqual(entries[0], response.context_data["entries_data"][2]["entry"])
        self.assertEqual(
            -3, response.context_data["entries_data"][2]["balance_at_date"]
        )

        self.assertEqual(entries[1], response.context_data["entries_data"][1]["entry"])
        self.assertEqual(
            -1, response.context_data["entries_data"][1]["balance_at_date"]
        )

        self.assertEqual(entries[2], response.context_data["entries_data"][0]["entry"])
        self.assertEqual(
            -2, response.context_data["entries_data"][0]["balance_at_date"]
        )

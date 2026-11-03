from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
)


class RecurringShiftWatchListView(TapirFactoryTestBase):
    VIEW_NAME = "shifts:shiftwatch_overview"

    def test_shiftWatchOverview_loggedInAsNormalUser_canSeeOwn(self):
        tapir_user = self.login_as_normal_user()
        response = self.client.get(reverse(self.VIEW_NAME, args=[tapir_user.id]))
        self.assertEqual(200, response.status_code)

    def test_shiftWatchOverview_loggedInAsNormalUser_cannotSeeOfOtherUser(self):
        self.login_as_normal_user()
        other_tapir_user = TapirUserFactory.create()
        response = self.client.get(reverse(self.VIEW_NAME, args=[other_tapir_user.id]))
        self.assertEqual(403, response.status_code)

    def test_shiftWatchOverview_loggedInAsMemberOffice_canSeeOfOtherUser(self):
        self.login_as_member_office_user()
        other_tapir_user = TapirUserFactory.create()

        response = self.client.get(reverse(self.VIEW_NAME, args=[other_tapir_user.id]))

        self.assertEqual(200, response.status_code)

    def test_shiftWatchOverview_loggedInAsVorstand_canSeeOfOtherUser(self):
        self.login_as_vorstand()
        other_tapir_user = TapirUserFactory.create()

        response = self.client.get(reverse(self.VIEW_NAME, args=[other_tapir_user.id]))

        self.assertEqual(200, response.status_code)

    def test_shiftWatchOverview_loggedInAsEmployee_canSeeLogOfOtherUser(self):
        self.login_as_employee()
        other_tapir_user = TapirUserFactory.create()

        response = self.client.get(reverse(self.VIEW_NAME, args=[other_tapir_user.id]))

        self.assertEqual(200, response.status_code)

from django.urls import reverse

from tapir import settings
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, PermissionTestMixin


class TestShiftDeleteView(PermissionTestMixin, TapirFactoryTestBase):
    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
            settings.GROUP_EMPLOYEES,
            settings.GROUP_MEMBER_OFFICE,
            settings.GROUP_SHIFT_MANAGER,
        ]

    def do_request(self):
        shift = ShiftFactory.create()

        return self.client.get(reverse("shifts:shift_delete", args=[shift.id]))

    def test_deleteShiftView_loggedInAsMemberOffice_shiftMarkedAsDeleted(self):
        self.login_as_member_office_user()
        shift = ShiftFactory.create()

        response = self.client.post(
            reverse("shifts:shift_delete", args=[shift.id]),
            data={"confirm_understood": True},
        )

        self.assertStatusCode(response, 302)
        self.assertRedirects(response, reverse("shifts:calendar"))
        shift.refresh_from_db()
        self.assertTrue(shift.deleted)

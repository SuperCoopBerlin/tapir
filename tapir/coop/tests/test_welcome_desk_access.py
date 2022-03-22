import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAttendance, Shift, ShiftSlot
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestWelcomeDeskAccess(TapirFactoryTestBase):
    def test_normal_user_no_access_without_shift(self):
        normal_user = self.login_as_normal_user()

        self.assertFalse(
            ShiftAttendance.objects.filter(user=normal_user).exists(),
            "We assume that the user starts without any shift attendance.",
        )

        start_time = timezone.now() + datetime.timedelta(hours=0, minutes=30)
        shift_not_now = ShiftFactory.create(
            start_time=start_time, end_time=start_time + datetime.timedelta(hours=3)
        )
        self.register_user_to_shift(normal_user, shift_not_now)

        response = self.client.get(reverse("accounts:user_me"), follow=True)
        # We check the user from the request because the permission is not part the user,
        # it only gets added by the middleware.
        self.assertFalse(
            response.context["request"].user.has_perm("welcomedesk.view"),
            "The user is not doing a shift at the moment, they should not have access to the welcome desk.",
        )
        self.assertNotIn(
            "welcome_desk_link",
            response.content.decode(),
            "The user should not have access to the welcome desk page, therefore the link should not be visible.",
        )

    def test_normal_user_access_with_shift(self):
        start_time = timezone.now() - datetime.timedelta(hours=1)
        shift_now = ShiftFactory.create(
            start_time=start_time, end_time=start_time + datetime.timedelta(hours=3)
        )

        normal_user = TapirUserFactory.create(is_in_member_office=False)
        self.login_as_member_office_user()
        self.register_user_to_shift(normal_user, shift_now)

        self.login_as_user(normal_user)
        response = self.client.get(reverse("accounts:user_me"), follow=True)

        self.assertTrue(
            response.context["request"].user.has_perm("welcomedesk.view"),
            "The user is doing a shift at the moment, they should have access to the welcome desk.",
        )
        self.assertIn(
            "welcome_desk_link",
            response.content.decode(),
            "The user should have access to the welcome desk page, therefore the link should be visible.",
        )

    def test_member_office_user(self):
        member_office_user = self.login_as_member_office_user()

        self.assertFalse(
            ShiftAttendance.objects.filter(user=member_office_user).exists(),
            "We assume that the user starts without any shift attendance.",
        )

        response = self.client.get(reverse("accounts:user_me"), follow=True)

        self.assertTrue(
            response.context["request"].user.has_perm("welcomedesk.view"),
            "Member office users should always have access to the welcome desk.",
        )
        self.assertIn(
            "welcome_desk_link",
            response.content.decode(),
            "The user should have access to the welcome desk page, therefore the link should be visible.",
        )

    def register_user_to_shift(self, user: TapirUser, shift: Shift):
        slot = ShiftSlot.objects.filter(shift=shift, attendances__isnull=True).first()
        self.client.post(
            reverse("shifts:slot_register", args=[slot.id]), {"user": user.id}
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(slot=slot, user=user).count(),
            1,
            "Registration should have worked",
        )

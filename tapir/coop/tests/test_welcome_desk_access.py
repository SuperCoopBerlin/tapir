import datetime

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.models import (
    ShiftAccountEntry,
    ShiftAttendance,
    ShiftAttendanceTemplate,
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestWelcomeDeskAccess(TapirSeleniumTestBase):
    @tag("selenium")
    def test_welcome_desk_access(self):
        standard_user = TapirUser.objects.get(
            username=self.get_standard_user().get_username()
        )
        self.login(standard_user.username, standard_user.username)

        ShiftAttendance.objects.filter(user=standard_user).delete()
        ShiftAttendanceTemplate.objects.filter(user=standard_user).delete()

        self.selenium.get(self.live_server_url + reverse("accounts:user_me"))
        self.wait_until_element_present_by_id("tapir_user_detail_card")
        self.assertFalse(
            self.does_element_exist_by_id("welcome_desk_link"),
            "The user has no special permissions and is not in a shift at the moment, should therefore not see the welcome desk link.",
        )

        shift = Shift.objects.create(
            start_time=timezone.now() - timezone.timedelta(hours=1),
            end_time=timezone.now() + timezone.timedelta(hours=1),
        )
        slot = ShiftSlot.objects.create(shift=shift)
        ShiftAttendance.objects.create(slot=slot, user=standard_user)

        self.selenium.get(self.live_server_url + reverse("coop:welcome_desk_search"))
        self.wait_until_element_present_by_id("welcome_desk_table")
        self.assertTrue(
            self.does_element_exist_by_id("welcome_desk_link"),
            "The user has just been registered to a shift that is happening now, they should see the welcome desk link.",
        )

        self.selenium.get(
            self.live_server_url
            + reverse("coop:welcome_desk_share_owner", args=[standard_user.pk])
        )
        self.wait_until_element_present_by_id("welcome_desk_share_owner")

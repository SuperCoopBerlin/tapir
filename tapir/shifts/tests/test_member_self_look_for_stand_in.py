from datetime import timedelta

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import (
    ShiftAttendance,
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestMemberSelfLookForStandIn(TapirSeleniumTestBase):
    @tag("selenium")
    def test_member_self_look_for_stand_in(self):
        user1 = self.get_standard_user()
        self.login(user1.get_username(), user1.get_username())

        start_time = timezone.now() + timedelta(
            days=Shift.NB_DAYS_FOR_SELF_UNREGISTER + 2
        )
        end_time = start_time + timedelta(hours=3)
        shift = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot = ShiftSlot.objects.create(shift=shift)
        self.selenium.get(
            self.live_server_url + reverse("shifts:shift_detail", args=[shift.pk])
        )
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_element_by_class_name("register-self-button").click()
        self.wait_until_element_present_by_id("self_look_for_stand_in_button")
        self.selenium.find_element_by_id("self_look_for_stand_in_button").click()
        self.wait_until_element_present_by_id("cancel_look_for_stand_in")

        self.logout_if_necessary()
        user2 = self.get_member_office_user()
        self.login(user2.get_username(), user2.get_username())
        self.selenium.get(
            self.live_server_url + reverse("shifts:shift_detail", args=[shift.pk])
        )
        self.selenium.find_element_by_class_name("register-self-button").click()
        self.assertEqual(
            ShiftAttendance.objects.filter(
                user=user2.get_tapir_user(),
                slot=slot,
                state=ShiftAttendance.State.PENDING,
            ).count(),
            1,
            "The second user should have taken over the shift slot and therefore should have a valid attendance",
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(
                user=user1.get_tapir_user(),
                slot=slot,
                state=ShiftAttendance.State.CANCELLED,
            ).count(),
            1,
            "The first user should have it's attendance cancelled because the second user took over the shift.",
        )

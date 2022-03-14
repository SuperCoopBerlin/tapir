import time
from datetime import timedelta

from django.test import tag
from django.urls import reverse
from django.utils import timezone
from selenium.webdriver.common.keys import Keys

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftAttendance,
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase, TAPIR_SELENIUM_BASE_FIXTURES


class TestMemberOfficeLookForStandInAndReplace(TapirSeleniumTestBase):
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES + [
        "test_member_office_look_for_stand_in_and_replace.json",
    ]

    @tag("selenium")
    def test_member_office_look_for_stand_in_and_replace(self):
        standard_user = self.get_standard_user()
        member_office_user = self.get_member_office_user()
        replacing_user = TapirUser.objects.get(username="hilla.waisanen")
        self.login(member_office_user.get_username(), member_office_user.get_username())

        start_time = timezone.now() + timedelta(
            days=Shift.NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN + 2
        )
        end_time = start_time + timedelta(hours=3)
        shift = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot = ShiftSlot.objects.create(shift=shift)
        ShiftAttendance.objects.create(slot=slot, user=standard_user.get_tapir_user())
        self.selenium.get(
            self.live_server_url + reverse("shifts:shift_detail", args=[shift.pk])
        )
        self.wait_until_element_present_by_id("shift_detail_card")
        self.selenium.find_element_by_class_name(
            "member-office-look-for-standin-button"
        ).click()
        self.wait_until_element_present_by_class_name("register-to-slot-button")
        self.selenium.find_element_by_class_name("register-to-slot-button").click()
        self.wait_until_element_present_by_id("register_to_shift_slot_card")
        self.selenium.find_element_by_id("select2-id_user-container").click()
        search_field = self.selenium.find_element_by_class_name("select2-search__field")
        search_field.send_keys(replacing_user.get_display_name())
        search_field.send_keys(Keys.ENTER)
        self.selenium.find_element_by_id("register_button").click()
        self.wait_until_element_present_by_id("shift_detail_card")
        self.assertEqual(
            ShiftAttendance.objects.filter(
                user=replacing_user,
                slot=slot,
                state=ShiftAttendance.State.PENDING,
            ).count(),
            1,
            "The replacing user should have taken over the shift slot and therefore should have a valid attendance",
        )
        self.assertEqual(
            ShiftAttendance.objects.filter(
                user=standard_user.get_tapir_user(),
                slot=slot,
                state=ShiftAttendance.State.CANCELLED,
            ).count(),
            1,
            "The original user should have it's attendance cancelled because the second user took over the shift.",
        )

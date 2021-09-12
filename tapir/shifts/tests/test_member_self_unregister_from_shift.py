import datetime
import time

import django.utils.timezone
from django.test import tag
from django.urls import reverse
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftAttendanceTemplate,
    ShiftAttendance,
    Shift,
    ShiftSlot,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase, TAPIR_SELENIUM_BASE_FIXTURES


class TestMemberSelfUnregisterToShift(TapirSeleniumTestBase):
    @tag("selenium")
    def test_member_self_unregister_from_shift(self):
        standard_user_json = self.get_standard_user()
        standard_user_tapir = TapirUser.objects.get(
            username=standard_user_json.get_username()
        )
        self.login(standard_user_json.get_username(), standard_user_json.get_username())
        attendance_template = ShiftAttendanceTemplate.objects.get(
            user=standard_user_tapir
        )

        for (
            shift
        ) in attendance_template.slot_template.shift_template.generated_shifts.all():
            self.check_can_unregister(shift, False)

        start_time = timezone.now() + datetime.timedelta(
            days=Shift.NB_DAYS_FOR_SELF_UNREGISTER - 2
        )
        end_time = start_time + datetime.timedelta(hours=3)
        shift_this_week = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot_this_week = ShiftSlot.objects.create(shift=shift_this_week)
        ShiftAttendance.objects.create(user=standard_user_tapir, slot=slot_this_week)
        self.assertFalse(
            slot_this_week.user_can_self_unregister(standard_user_tapir),
            "The user should not be able to unregister themselves because the shift is too close to now",
        )
        self.check_can_unregister(shift_this_week, False)

        start_time = timezone.now() + datetime.timedelta(
            days=Shift.NB_DAYS_FOR_SELF_UNREGISTER + 2
        )
        end_time = start_time + datetime.timedelta(hours=3)
        shift_next_week = Shift.objects.create(start_time=start_time, end_time=end_time)
        slot_next_week = ShiftSlot.objects.create(shift=shift_next_week)
        ShiftAttendance.objects.create(user=standard_user_tapir, slot=slot_next_week)
        self.assertTrue(
            slot_next_week.user_can_self_unregister(standard_user_tapir),
            "The user should be able to unregister themselves because the shift is later than Shift.NB_DAYS_FOR_SELF_UNREGISTER",
        )
        self.check_can_unregister(shift_next_week, True)

    def check_can_unregister(self, shift: Shift, must_be_able_to_unregister: bool):
        self.selenium.get(self.live_server_url + shift.get_absolute_url())
        self.wait_until_element_present_by_id("shift_card_title")

        self.assertEqual(
            len(self.selenium.find_elements_by_id("unregister_self_button")),
            1 if must_be_able_to_unregister else 0,
        )

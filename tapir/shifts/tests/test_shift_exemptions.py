import datetime

import django.utils.translation
from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftExemption,
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftTemplate,
    ShiftSlotTemplate,
    ShiftTemplateGroup,
)
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestShiftExemptions(TapirSeleniumTestBase):
    @tag("selenium")
    def test_member_exempted_from_shifts(self):
        member_office_user_json = self.get_member_office_user()
        self.login(
            member_office_user_json.get_username(),
            member_office_user_json.get_username(),
        )
        standard_user_json = self.get_standard_user()
        standard_user_tapir = standard_user_json.get_tapir_user()

        ShiftExemption.objects.filter(
            shift_user_data__user=standard_user_tapir
        ).delete()
        ShiftAttendance.objects.filter(user=standard_user_tapir).delete()
        ShiftAttendanceTemplate.objects.filter(user=standard_user_tapir).delete()

        self.check_is_exempted(standard_user_tapir, None)

        start_date = timezone.now() - datetime.timedelta(days=7)
        end_date = timezone.now() - datetime.timedelta(days=2)
        description = "AN_EXEMPTION_IN_THE_PAST"
        self.create_exemption(
            standard_user_tapir, start_date, end_date, description, None, None
        )
        self.check_is_exempted(standard_user_tapir, None)

        start_date = timezone.now() - datetime.timedelta(days=4)
        end_date = timezone.now() + datetime.timedelta(days=3)
        description = "AN_EXEMPTION_THAT_IS_ACTIVE"
        exemption = self.create_exemption(
            standard_user_tapir, start_date, end_date, description, None, None
        )
        self.check_is_exempted(standard_user_tapir, exemption)

        shift_template = ShiftTemplate.objects.create(
            weekday=0,
            start_time=datetime.time(hour=8, minute=0),
            end_time=datetime.time(hour=9, minute=0),
            group=ShiftTemplateGroup.objects.first(),
        )
        slot_template = ShiftSlotTemplate.objects.create(shift_template=shift_template)
        ShiftAttendanceTemplate.objects.create(
            user=standard_user_tapir, slot_template=slot_template
        )
        shifts_deleted_by_short_exemption = []
        shifts_deleted_by_long_exemption = []
        for days in [10, 50, 100, 365]:
            shift = shift_template.create_shift(
                start_date=datetime.date.today() + datetime.timedelta(days=days)
            )
            if days in [50]:
                shifts_deleted_by_short_exemption.append(shift)
            if days in [100]:
                shifts_deleted_by_long_exemption.append(shift)

        start_date = datetime.date.today() + datetime.timedelta(days=40)
        end_date = datetime.date.today() + datetime.timedelta(days=60)
        self.create_exemption(
            standard_user_tapir,
            start_date,
            end_date,
            "A_SHORT_EXEMPTION",
            shifts_deleted_by_short_exemption,
            None,
        )

        self.assertEqual(
            3,
            ShiftAttendance.objects.filter(user=standard_user_tapir)
            .with_valid_state()
            .count(),
            "One attendance should have been cancelled because it's covered by the exemption, the others should still "
            "be there",
        )
        self.assertEqual(
            1,
            ShiftAttendanceTemplate.objects.filter(user=standard_user_tapir).count(),
            "The exemption is shorter than 6 cycles, the user should still have it's attendance template",
        )

        start_date = datetime.date.today() + datetime.timedelta(days=70)
        end_date = datetime.date.today() + datetime.timedelta(days=270)
        self.create_exemption(
            standard_user_tapir,
            start_date,
            end_date,
            "A_LONG_EXEMPTION",
            shifts_deleted_by_long_exemption,
            ShiftAttendanceTemplate.objects.filter(user=standard_user_tapir),
        )

        self.assertEqual(
            1,
            ShiftAttendance.objects.filter(user=standard_user_tapir)
            .with_valid_state()
            .count(),
            "Only one attendance should be left, the one that is before both attendances. The one at 365 days is not "
            "covered by an exemption, but is lost along with the slot_template loss.",
        )
        self.assertEqual(
            0,
            ShiftAttendanceTemplate.objects.filter(user=standard_user_tapir).count(),
            "The exemption is longer than 6 cycles, the user should have lost it's attendance template",
        )

    def create_exemption(
        self,
        user: TapirUser,
        start_date,
        end_date,
        description: str,
        attendances,
        attendance_templates,
    ) -> ShiftExemption:
        self.selenium.get(
            self.live_server_url + reverse("accounts:user_detail", args=[user.id])
        )
        self.wait_until_element_present_by_id("shift_exemption_list_button")
        self.selenium.find_element_by_id("shift_exemption_list_button").click()
        self.wait_until_element_present_by_id("shift_exemptions_table")
        self.selenium.find_element_by_id("create_shift_exemption_button").click()
        self.wait_until_element_present_by_id("shift_exemption_form")
        self.fill_date_field("id_start_date", start_date)
        self.fill_date_field("id_end_date", end_date)
        self.selenium.find_element_by_id("id_description").send_keys(description)

        if attendances is None:
            self.assertEqual(
                "hidden",
                self.selenium.find_element_by_id(
                    "id_confirm_cancelled_attendances"
                ).get_attribute("type"),
                "No attendance is expected to be deleted, therefore the warning should not be displayed",
            )

        if attendance_templates is None:
            self.assertEqual(
                "hidden",
                self.selenium.find_element_by_id(
                    "id_confirm_cancelled_abcd_attendances"
                ).get_attribute("type"),
                "No attendance_template is expected to be deleted, therefore the warning should not be displayed",
            )

        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

        if attendances is None and attendance_templates is None:
            self.wait_until_element_present_by_id("shift_exemption_list_button")
            return ShiftExemption.objects.get(description=description)

        if attendances is not None:
            self.selenium.find_element_by_id("id_confirm_cancelled_attendances").click()
            for attendance in attendances:
                self.assertTrue(
                    attendance.get_display_name() in self.selenium.page_source,
                    f"There should be a warning that the following attendance will be deleted: "
                    f"{attendance.get_display_name()}",
                )

        if attendance_templates is not None:
            self.selenium.find_element_by_id(
                "id_confirm_cancelled_abcd_attendances"
            ).click()
            for attendance_template in attendance_templates:
                with django.utils.translation.override("en"):
                    display_name = attendance_template.slot_template.get_display_name()
                self.assertTrue(
                    display_name in self.selenium.page_source,
                    f"There should be a warning that the following attendance template will be deleted: "
                    f"{display_name}",
                )

        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()
        self.wait_until_element_present_by_id("shift_exemption_list_button")
        return ShiftExemption.objects.get(description=description)

    def check_is_exempted(self, user: TapirUser, exemption: ShiftExemption):
        self.assertEqual(
            exemption is not None,
            user.shift_user_data.is_currently_exempted_from_shifts(),
        )
        self.selenium.get(
            self.live_server_url + reverse("accounts:user_detail", args=[user.id])
        )

        if exemption is None:
            self.assertEqual(
                "None", self.selenium.find_element_by_id("shift_exemption_value").text
            )
        else:
            self.assertIn(
                exemption.description,
                self.selenium.find_element_by_id("shift_exemption_value").text,
            )
            self.assertIn(
                exemption.end_date.strftime("%d.%m.%y"),
                self.selenium.find_element_by_id("shift_exemption_value").text,
            )

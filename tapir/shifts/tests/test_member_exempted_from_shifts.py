import datetime

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import ShiftExemption
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestMemberExemptedFromShifts(TapirSeleniumTestBase):
    @tag("selenium")
    def test_member_exempted_from_shifts(self):
        member_office_user_json = self.get_member_office_user()
        self.login(
            member_office_user_json.get_username(),
            member_office_user_json.get_username(),
        )
        standard_user_json = self.get_standard_user()
        standard_user_tapir = standard_user_json.get_tapir_user()
        self.assertEqual(
            0,
            ShiftExemption.objects.filter(
                shift_user_data__user=standard_user_tapir
            ).count(),
            "The test expects that the users starts without any exemption",
        )

        self.check_is_exempted(standard_user_tapir, None)

        start_date = timezone.now() - datetime.timedelta(days=7)
        end_date = timezone.now() - datetime.timedelta(days=2)
        description = "AN_EXEMPTION_IN_THE_PAST"
        self.create_exemption(standard_user_tapir, start_date, end_date, description)
        self.check_is_exempted(standard_user_tapir, None)

        start_date = timezone.now() - datetime.timedelta(days=4)
        end_date = timezone.now() + datetime.timedelta(days=3)
        description = "AN_EXEMPTION_THAT_IS_ACTIVE"
        exemption = self.create_exemption(
            standard_user_tapir, start_date, end_date, description
        )
        self.check_is_exempted(standard_user_tapir, exemption)

    def create_exemption(
        self, user: TapirUser, start_date, end_date, description: str
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

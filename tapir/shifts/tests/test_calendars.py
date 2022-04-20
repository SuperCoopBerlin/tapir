from django.urls import reverse

from tapir.shifts.models import ShiftTemplateGroup
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCalendars(TapirFactoryTestBase):
    # Minimal tests that the calendar views works, some of them were broken but the tests were still green.

    def test_calendar_future_view_response_status_200(self):
        self.login_as_normal_user()
        response = self.client.get(reverse("shifts:calendar_future"))
        self.assertEqual(response.status_code, 200)

    def test_calendar_past_view_response_status_200(self):
        self.login_as_member_office_user()
        response = self.client.get(reverse("shifts:calendar_past"))
        self.assertEqual(response.status_code, 200)

    def test_shift_template_overview_view_response_status_200(self):
        self.login_as_normal_user()
        response = self.client.get(reverse("shifts:shift_template_overview"))
        self.assertEqual(response.status_code, 200)

    def test_shift_template_group_calendar_view_response_status_200(self):
        self.login_as_normal_user()
        for name in ["A", "B"]:
            ShiftTemplateGroup.objects.create(name=name)
        response = self.client.get(reverse("shifts:shift_template_group_calendar"))
        self.assertEqual(response.status_code, 200)

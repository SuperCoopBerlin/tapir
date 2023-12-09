import datetime

from django.urls import reverse

from tapir.shifts.models import ShiftTemplateGroup
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCalendars(TapirFactoryTestBase):
    # Minimal tests that the calendar views works, some of them were broken but the tests were still green.

    def test_calendar_view_response_status_200(self):
        self.login_as_normal_user()
        response = self.client.get(reverse("shifts:calendar"))
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

    def test_day_printable_view_status_200(self):
        self.login_as_member_office_user()
        ShiftFactory(start_time=datetime.datetime(year=2023, month=6, day=15, hour=12))
        response = self.client.get(
            reverse("shifts:shift_day_printable", args=["15-06-23"])
        )
        self.assertEqual(response.status_code, 200)

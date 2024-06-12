import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.shifts.models import (
    Shift,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCreate(TapirFactoryTestBase):
    SHIFT_CREATE_VIEW = "shifts:create_shift"
    SHIFT_NAME = "Test shift"
    SHIFT_START_TIME = datetime.datetime(
        year=2022,
        month=6,
        day=1,
        hour=8,
        minute=0,
        tzinfo=timezone.get_current_timezone(),
    )
    SHIFT_REQUIRED_ATTENDANCES = 3
    SHIFT_DESCRIPTION = "A test description."

    def test_member_office_can_create_shifts(self):
        self.login_as_member_office_user()
        self._assert_can_create_shifts()

    def test_shift_manager_can_create_shifts(self):
        self.login_as_shift_manager()
        self._assert_can_create_shifts()

    def _assert_can_create_shifts(self):
        end_time = self.SHIFT_START_TIME + datetime.timedelta(hours=3)
        response = self.client.post(
            reverse(self.SHIFT_CREATE_VIEW, args=[]),
            {
                "name": self.SHIFT_NAME,
                "start_time": self.SHIFT_START_TIME,
                "end_time": end_time,
                "num_required_attendances": self.SHIFT_REQUIRED_ATTENDANCES,
                "description": self.SHIFT_DESCRIPTION,
                "warning_time": datetime.timedelta(days=-1),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Shift.objects.count(), 1)

        shift = Shift.objects.all().first()
        self.assertEqual(shift.name, self.SHIFT_NAME)
        self.assertEqual(shift.start_time, self.SHIFT_START_TIME)
        self.assertEqual(shift.end_time, end_time)
        self.assertEqual(
            shift.num_required_attendances, self.SHIFT_REQUIRED_ATTENDANCES
        )
        self.assertEqual(shift.description, self.SHIFT_DESCRIPTION)

    def test_normal_user_access_denied(self):
        self.login_as_normal_user()

        end_time = self.SHIFT_START_TIME + datetime.timedelta(hours=3)
        response = self.client.post(
            reverse(self.SHIFT_CREATE_VIEW, args=[]),
            {
                "name": self.SHIFT_NAME,
                "start_time": self.SHIFT_START_TIME,
                "end_time": end_time,
                "num_required_attendances": self.SHIFT_REQUIRED_ATTENDANCES,
                "description": self.SHIFT_DESCRIPTION,
            },
        )

        self.assertEqual(
            response.status_code,
            403,
            "A user that is not in the member should not have access to shift creation.",
        )

    def test_end_time_cant_be_before_start_time(self):
        self.login_as_member_office_user()

        end_time = self.SHIFT_START_TIME - datetime.timedelta(hours=3)

        self.client.post(
            reverse(self.SHIFT_CREATE_VIEW, args=[]),
            {
                "name": self.SHIFT_NAME,
                "start_time": self.SHIFT_START_TIME,
                "end_time": end_time,
                "num_required_attendances": self.SHIFT_REQUIRED_ATTENDANCES,
                "description": self.SHIFT_DESCRIPTION,
            },
            follow=True,
        )

        self.assertEqual(Shift.objects.count(), 0)

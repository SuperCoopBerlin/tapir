import pytest
from django.urls import reverse

from tapir.shifts.models import StaffingStatusChoices, ShiftWatch
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCancel(TapirFactoryTestBase):

    def test_shift_watch_form_creates_shift_watch_instance(self):
        user = self.login_as_normal_user()
        shift = ShiftFactory.create()

        staffing_status_choices = [
            StaffingStatusChoices.FULL,
            StaffingStatusChoices.UNDERSTAFFED,
        ]
        response = self.client.post(
            reverse(viewname="shifts:watch_shift", args=[shift.id]),
            data={
                "staffing_status": staffing_status_choices,
            },
        )
        print(ShiftWatch.objects.all().values())
        self.assertRedirects(
            response,
            shift.get_absolute_url(),
            msg_prefix="The request should redirect to the shift's page.",
        )

        self.assertEqual(
            ShiftWatch.objects.count(),
            1,
        )
        shift_watch_instance = ShiftWatch.objects.first()
        self.assertEqual(shift_watch_instance.user, user)
        self.assertEqual(shift_watch_instance.shift, shift)
        self.assertEqual(
            set(shift_watch_instance.staffing_status), set(staffing_status_choices)
        )

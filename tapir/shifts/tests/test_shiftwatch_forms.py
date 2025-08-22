import pytest
from django.urls import reverse

from tapir.shifts.models import StaffingEventsChoices, ShiftWatch
from tapir.shifts.tests.factories import ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCancel(TapirFactoryTestBase):

    @pytest.mark.django_db
    def test_shift_watch_form_creates_shift_watch_instance(self):
        user = self.login_as_normal_user()
        shift = ShiftFactory.create()

        staffing_event_choices = [
            StaffingEventsChoices.FULL,
            StaffingEventsChoices.UNDERSTAFFED,
        ]
        response = self.client.post(
            reverse(viewname="shifts:watch_shift", args=[shift.id]),
            data={
                "staffing_events": staffing_event_choices,
            },
        )
        print(ShiftWatch.objects.all().values())
        self.assertRedirects(
            response,
            shift.get_absolute_url(),
            msg_prefix="The request should redirect to the shift's page.",
        )

        assert ShiftWatch.objects.count() == 1
        shift_watch_instance = ShiftWatch.objects.first()
        assert shift_watch_instance.user == user
        assert shift_watch_instance.shift == shift
        assert set(shift_watch_instance.staffing_events) == set(staffing_event_choices)

import datetime

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from django_extensions.jobs import weekly

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.shifts.tests.utils import register_user_to_shift_template
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftTemplateEndView(TapirFactoryTestBase):

    def setUp(self):
        super().setUp()
        self.shift_template = ShiftTemplateFactory.create(
            start_date=timezone.now().date(), weekday=0
        )
        self.url = reverse(
            "shifts:shift_template_set_end_date", kwargs={"pk": self.shift_template.pk}
        )

    def test_shiftTemplate_setEndDateInBetween_futureShiftsAfterEndDateAreCancelled(
        self,
    ):
        self.login_as_employee()

        user = TapirUserFactory.create(is_in_member_office=False)
        register_user_to_shift_template(self.client, user, self.shift_template)

        today = timezone.now().date()
        shift_1 = self.shift_template.create_shift_if_necessary(
            today + datetime.timedelta(days=7)
        )
        shift_2 = self.shift_template.create_shift_if_necessary(
            today + datetime.timedelta(days=14)
        )
        shift_3 = self.shift_template.create_shift_if_necessary(
            today + datetime.timedelta(days=21)
        )

        end_date = today + datetime.timedelta(days=14)
        cancellation_reason = "Shift Template ended"

        response = self.client.post(
            self.url,
            {
                "end_date": end_date.strftime("%Y-%m-%d"),
                "cancellation_reason": cancellation_reason,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "shifts:shift_template_detail", kwargs={"pk": self.shift_template.pk}
            ),
        )

        self.shift_template.refresh_from_db()
        shift_1.refresh_from_db()
        shift_2.refresh_from_db()
        shift_3.refresh_from_db()

        self.assertEqual(self.shift_template.end_date, end_date)

        self.assertFalse(shift_1.cancelled)
        self.assertFalse(shift_2.cancelled)

        self.assertTrue(shift_3.cancelled)
        self.assertEqual(shift_3.cancelled_reason, cancellation_reason)

    def test_shiftTemplate_sendEndDateAfterAllShifts_noShiftIsCancelled(self):
        self.login_as_employee()
        today = timezone.now().date()
        end_date = today + datetime.timedelta(days=365)
        cancellation_reason = "Shift Template ended"
        shift = self.shift_template.create_shift_if_necessary(
            today + datetime.timedelta(days=7)
        )

        response = self.client.post(
            self.url,
            {
                "end_date": end_date.strftime("%Y-%m-%d"),
                "cancellation_reason": cancellation_reason,
            },
        )

        self.shift_template.refresh_from_db()
        shift.refresh_from_db()
        self.assertEqual(self.shift_template.end_date, end_date)

        self.assertFalse(shift.cancelled)

        msgs = list(get_messages(response.wsgi_request))
        self.assertGreater(len(msgs), 0)

    def test_shiftTemplate_sendEndDate_endDateBeforeStartDate_showsValidationError(
        self,
    ):
        self.login_as_employee()

        end_date = self.shift_template.start_date - datetime.timedelta(days=7)

        response = self.client.post(
            self.url,
            {
                "end_date": end_date.strftime("%Y-%m-%d"),
                "cancellation_reason": "Test",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("end_date", response.context["form"].errors)

        self.shift_template.refresh_from_db()
        self.assertIsNone(self.shift_template.end_date)

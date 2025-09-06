import datetime

import pytest
from celery.states import state
from django.core.management import call_command
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftTemplate, ShiftAttendance, Shift
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.shifts.views import ShiftDetailView
from tapir.utils.tests_utils import TapirFactoryTestBase


class ShiftGetPastShiftsStatisticsTests(TapirFactoryTestBase):

    def test_getPastShiftsData_DifferentStatesOfAttendandance_onlyCountDoneState(self):
        user_done = TapirUserFactory.create()
        user_excused = TapirUserFactory.create()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=2)
        shift = ShiftFactory(
            start_time=timezone.now() - datetime.timedelta(days=1),
            nb_slots=2,
            shift_template=shift_template,
        )

        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.DONE, user=user_done, slot=shift.slots.all()[0]
        )
        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.MISSED_EXCUSED,
            user=user_excused,
            slot=shift.slots.all()[1],
        )

        context = ShiftDetailView.get_past_shifts_data(shift)
        self.assertEqual(context["no_of_past_shifts"], 1)
        self.assertEqual(context["total_valid_attendances"], 1)
        self.assertEqual(
            context["total_hours"],
            (shift.end_time - shift.start_time).total_seconds() / 3600,
        )

    def test_getPastShiftsData_MultipleAttendandances_correctValues(self):
        users = [TapirUserFactory.create() for _ in range(5)]
        shift_template = ShiftTemplateFactory.create(nb_slots=len(users))
        shifts = [
            ShiftFactory(
                start_time=timezone.now() - datetime.timedelta(days=i + 1),
                nb_slots=len(users),
                shift_template=shift_template,
            )
            for i in range(5)
        ]

        for shift in shifts:
            slots = list(shift.slots.all())
            for i, user in enumerate(users):
                ShiftAttendance.objects.create(
                    state=ShiftAttendance.State.DONE, user=user, slot=slots[i]
                )
        context = ShiftDetailView.get_past_shifts_data(shifts[-1])

        self.assertEqual(context["no_of_past_shifts"], len(shifts))
        self.assertEqual(context["total_valid_attendances"], len(users) * len(shifts))
        self.assertEqual(
            context["total_hours"],
            len(users)
            * sum(
                (shift.end_time - shift.start_time).total_seconds() / 3600
                for shift in shifts
            ),
        )

    # def test_no_past_shifts(self):
    #     # Create a future shift
    #     future_shift = ShiftFactory.create(
    #         start_time=self.REFERENCE_TIME + datetime.timedelta(days=1),
    #         end_time=self.REFERENCE_TIME + datetime.timedelta(days=2),
    #         shift_template=self.shift_template
    #     )
    #
    #     # Create an instance of the view
    #     view = ShiftDetailView()
    #     context = {}
    #
    #     # Call the method to test
    #     view.get_past_shifts_data(future_shift, context)
    #
    #     # Assertions
    #     self.assertEqual(context["no_of_past_shifts"], 0)
    #     self.assertNotIn("total_valid_attendances", context)
    #     self.assertNotIn("total_hours", context)

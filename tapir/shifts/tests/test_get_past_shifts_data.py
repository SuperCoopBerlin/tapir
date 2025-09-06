import datetime

from celery.states import state
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
        shift = shift_template.create_shift(
            timezone.now().date() - datetime.timedelta(days=2)
        )

        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.DONE, user=user_done, slot=shift.slots.all()[0]
        )
        ShiftAttendance.objects.create(
            state=ShiftAttendance.State.MISSED_EXCUSED,
            user=user_excused,
            slot=shift.slots.all()[1],
        )
        print(ShiftAttendance.objects.all().values())

        context = {}
        ShiftDetailView.get_past_shifts_data(shift, context=context)
        self.assertEqual(context["no_of_past_shifts"], 1)
        self.assertEqual(context["total_valid_attendances"], 1)
        self.assertEqual(
            context["total_hours"],
            (shift.end_time - shift.start_time).total_seconds() / 3600,
        )

    #
    def test_getPastShiftsData_MultipleAttendandances_correctValues(self):
        users = [TapirUserFactory.create(is_in_member_office=False) for _ in range(5)]
        shift_template = ShiftTemplateFactory.create(nb_slots=len(users))
        shifts = [
            shift_template.create_shift(
                timezone.now().date() - datetime.timedelta(days=i)
            )
            for i in range(5)
        ]

        for shift in shifts:
            slots = list(shift.slots.all())
            for i, user in enumerate(users):
                ShiftAttendance.objects.create(
                    state=ShiftAttendance.State.DONE, user=user, slot=slots[i]
                )

        context = {}
        ShiftDetailView.get_past_shifts_data(shifts[-1], context=context)

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

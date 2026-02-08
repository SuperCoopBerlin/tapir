import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftAttendance,
    Shift,
)
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.shifts.views import ShiftDetailView
from tapir.utils.tests_utils import TapirFactoryTestBase


class ShiftGetPastShiftsStatisticsTests(TapirFactoryTestBase):

    def test_getPastShiftsData_differentStatesOfAttendandance_onlyCountDoneState(self):
        user_done = TapirUserFactory.create()
        user_excused = TapirUserFactory.create()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(nb_slots=2)
        shift: Shift = ShiftFactory.create(
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

        context = ShiftDetailView.get_past_shifts_data(shift.shift_template)
        self.assertEqual(context["no_of_past_shifts"], 1)
        self.assertEqual(context["total_valid_attendances"], 1)
        self.assertEqual(
            context["total_hours"],
            (shift.end_time - shift.start_time).total_seconds() / 3600,
        )

    def test_getPastShiftsData_multipleAttendandances_correctValues(self):
        users = TapirUserFactory.create_batch(5)
        shift_template = ShiftTemplateFactory.create(nb_slots=len(users))
        shifts: list[Shift] = [
            ShiftFactory.create(
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
        context = ShiftDetailView.get_past_shifts_data(shift_template)

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

    def test_get_past_shifts_data_changedShiftTemplateDuration_correctSum(self):
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_time=datetime.time(hour=10, tzinfo=datetime.timezone.utc),
            end_time=datetime.time(hour=12, tzinfo=datetime.timezone.utc),
        )
        shift_2_hours = shift_template.create_shift_if_necessary(
            timezone.now() - datetime.timedelta(days=7)
        )
        ShiftAttendance.objects.create(
            user=TapirUserFactory.create(),
            slot=shift_2_hours.slots.first(),
            state=ShiftAttendance.State.DONE,
        )

        shift_template.end_time = datetime.time(hour=15, tzinfo=datetime.timezone.utc)
        shift_template.save()

        shift_5_hours = shift_template.create_shift_if_necessary(
            timezone.now() - datetime.timedelta(days=14)
        )
        ShiftAttendance.objects.create(
            user=TapirUserFactory.create(),
            slot=shift_5_hours.slots.first(),
            state=ShiftAttendance.State.DONE,
        )

        context = ShiftDetailView.get_past_shifts_data(shift_template)
        self.assertAlmostEqual(context["total_hours"], 7.0)

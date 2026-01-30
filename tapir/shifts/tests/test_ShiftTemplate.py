import datetime

from tapir.shifts.models import Shift
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftTemplate(TapirFactoryTestBase):
    NAME = "test_name"
    START_TIME = datetime.time(hour=11, minute=47, tzinfo=datetime.timezone.utc)
    END_TIME = datetime.time(hour=13, minute=26, tzinfo=datetime.timezone.utc)
    DESCRIPTION = "test_description"
    NUM_REQUIRED_ATTENDANCES = 6
    CREATION_DATE = datetime.date(year=2023, month=8, day=7)
    WEEKDAY = 3
    ACTUAL_DATE_SHIFT_DATE = datetime.date(year=2023, month=8, day=10)

    def test_createShiftIfNecessary_shiftIsNotAlreadyGenerated_shiftGetsCreatedWithCorrectData(
        self,
    ):
        shift_template = ShiftTemplateFactory.create(
            name=self.NAME,
            start_time=self.START_TIME,
            end_time=self.END_TIME,
            description=self.DESCRIPTION,
            num_required_attendances=self.NUM_REQUIRED_ATTENDANCES,
            weekday=self.WEEKDAY,
        )
        self.assertEqual(0, Shift.objects.count())
        shift_template.create_shift_if_necessary(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())

        shift: Shift = Shift.objects.first()
        self.assertEqual(self.NAME, shift.name)
        self.assertEqual(self.DESCRIPTION, shift.description)
        self.assertEqual(self.NUM_REQUIRED_ATTENDANCES, shift.num_required_attendances)
        self.assertEqual(self.ACTUAL_DATE_SHIFT_DATE, shift.start_time.date())
        self.assertEqual(self.WEEKDAY, shift.start_time.weekday())
        self.assertEqual(self.START_TIME, shift.start_time.timetz())
        self.assertEqual(self.ACTUAL_DATE_SHIFT_DATE, shift.end_time.date())
        self.assertEqual(self.END_TIME, shift.end_time.timetz())

    def test_createShiftIfNecessary_shiftIsAlreadyGenerated_noNewShiftCreated(self):
        shift_template = ShiftTemplateFactory.create()
        self.assertEqual(0, Shift.objects.count())
        shift_template.create_shift_if_necessary(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())
        shift_template.create_shift_if_necessary(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())

    def test_createShiftIfNecessary_shiftAlreadyExistsOnTheSameDay_noNewShiftCreated(
        self,
    ):
        # Making sure that the shift template checks for any shift existing on the given day.
        # It can happen that the time of a single generated shift gets updated on a given day,
        # In that case the shift template should not generate another shift on that day.
        shift_template = ShiftTemplateFactory.create(
            start_time=datetime.time(hour=12, minute=0)
        )
        self.assertEqual(0, Shift.objects.count())
        shift_template.create_shift_if_necessary(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())

        shift = shift_template.generated_shifts.get()
        shift.start_time = shift.start_time.replace(hour=16)
        shift.save()

        shift_template.create_shift_if_necessary(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())

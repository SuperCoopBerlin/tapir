import datetime

from tapir.shifts.models import ShiftTemplate, Shift
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

    def test_createShift_shiftIsNotAlreadyGenerated_shiftGetsCreatedWithCorrectData(
        self,
    ):
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            name=self.NAME,
            start_time=self.START_TIME,
            end_time=self.END_TIME,
            description=self.DESCRIPTION,
            num_required_attendances=self.NUM_REQUIRED_ATTENDANCES,
            weekday=self.WEEKDAY,
        )
        self.assertEqual(0, Shift.objects.count())
        shift_template.create_shift(start_date=self.CREATION_DATE)
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

    def test_createShift_shiftIsAlreadyGenerated_noNewShiftCreated(self):
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        self.assertEqual(0, Shift.objects.count())
        shift_template.create_shift(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())
        shift_template.create_shift(start_date=self.CREATION_DATE)
        self.assertEqual(1, Shift.objects.count())

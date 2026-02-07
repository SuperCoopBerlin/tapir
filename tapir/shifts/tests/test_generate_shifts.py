import datetime
from unittest.mock import patch

from django.core.management import call_command

from tapir.shifts.models import ShiftTemplateGroup, ShiftTemplate
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestGenerateShifts(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=8, day=7, hour=10, minute=7)

    def setUp(self) -> None:
        super().setUp()
        patcher = patch("django.utils.timezone.now")
        self.mock_now = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_now.return_value = self.NOW
        for name in ["A", "B", "C", "D"]:
            ShiftTemplateGroup.objects.create(name=name)

    def test_shiftTemplateWithoutStartDate_generatesShiftsFromToday(self):
        weekday = 1
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            group=ShiftTemplateGroup.objects.get(name="B"), weekday=weekday
        )
        call_command("generate_shifts")
        self.assertEqual(8, shift_template.generated_shifts.count())
        self.assertEqual(
            (self.NOW + datetime.timedelta(days=weekday)).date(),
            shift_template.generated_shifts.order_by("start_time")
            .first()
            .start_time.date(),
        )

    def test_shiftTemplateWithStartDate_generatesShiftsFromStartDate(self):
        weekday = 1
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            group=ShiftTemplateGroup.objects.get(name="B"),
            weekday=weekday,
            start_date=datetime.date(year=2023, month=10, day=1),
        )
        call_command("generate_shifts")
        self.assertEqual(6, shift_template.generated_shifts.count())
        self.assertEqual(
            datetime.date(year=2023, month=10, day=3),
            shift_template.generated_shifts.order_by("start_time")
            .first()
            .start_time.date(),
        )

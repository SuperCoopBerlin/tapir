import datetime

from tapir.shifts.models import (
    ShiftTemplateGroup,
)
from tapir.shifts.utils import get_week_group
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestExemptions(TapirFactoryTestBase):
    CYCLE_START_DATES = [
        datetime.date(year=2022, month=4, day=11),
        datetime.date(year=2023, month=5, day=22),
        datetime.date(year=2025, month=2, day=3),
    ]

    def setUp(self) -> None:
        super().setUp()
        for name in ["A", "B", "C", "D"]:
            ShiftTemplateGroup.objects.create(name=name)

    def test_week_group_before(self):
        week_group = get_week_group(
            datetime.date(year=2022, month=3, day=28), self.CYCLE_START_DATES
        )
        self.assertIsNotNone(week_group)
        self.assertEqual(week_group.name, "C")

    def test_week_group_current(self):
        week_group = get_week_group(
            datetime.date(year=2022, month=9, day=19), self.CYCLE_START_DATES
        )
        self.assertIsNotNone(week_group)
        self.assertEqual(week_group.name, "D")

    def test_week_group_future(self):
        week_group = get_week_group(
            datetime.date(year=2025, month=2, day=10), self.CYCLE_START_DATES
        )
        self.assertIsNotNone(week_group)
        self.assertEqual(week_group.name, "B")

    def test_week_group_equal(self):
        week_group = get_week_group(self.CYCLE_START_DATES[1], self.CYCLE_START_DATES)
        self.assertIsNotNone(week_group)
        self.assertEqual(week_group.name, "A")

import datetime
from unittest.mock import patch, Mock, call

from django.test import SimpleTestCase

from tapir.shifts.services.shift_generator import ShiftGenerator


class TestGenerateShiftsUpTo(SimpleTestCase):
    @patch("tapir.shifts.services.shift_generator.get_week_group", autospec=True)
    @patch.object(ShiftGenerator, "create_shifts_for_group", autospec=True)
    def test_generateShiftsUpTo_noGroupFilter_createsShiftsOnAllWeeks(
        self, mock_create_shifts_for_group: Mock, mock_get_week_group: Mock
    ):
        week_group = Mock()
        mock_get_week_group.return_value = week_group

        ShiftGenerator.generate_shifts_up_to(
            start_date=datetime.date(2025, 10, 20),
            end_date=datetime.date(2025, 11, 16),
        )

        mondays = [
            datetime.date(2025, 10, 20),
            datetime.date(2025, 10, 27),
            datetime.date(2025, 11, 3),
            datetime.date(2025, 11, 10),
        ]

        self.assertEqual(4, mock_get_week_group.call_count)
        mock_get_week_group.assert_has_calls([call(monday) for monday in mondays])

        self.assertEqual(4, mock_create_shifts_for_group.call_count)
        mock_create_shifts_for_group.assert_has_calls(
            [
                call(at_date=monday, group=week_group, filter_shift_template_ids=None)
                for monday in mondays
            ]
        )

    @patch("tapir.shifts.services.shift_generator.get_week_group", autospec=True)
    @patch.object(ShiftGenerator, "create_shifts_for_group", autospec=True)
    def test_generateShiftsUpTo_withGroupFilter_createsShiftsOnlyOnFilteredWeeks(
        self, mock_create_shifts_for_group: Mock, mock_get_week_group: Mock
    ):
        week_group_a = Mock()
        week_group_a.id = 1
        week_group_b = Mock()
        week_group_b.id = 2
        mock_get_week_group.side_effect = lambda date: (
            week_group_a if date == datetime.date(2025, 10, 20) else week_group_b
        )

        ShiftGenerator.generate_shifts_up_to(
            start_date=datetime.date(2025, 10, 20),
            end_date=datetime.date(2025, 10, 27),
            filter_group_ids={1},
            filter_shift_template_ids={3, 4},
        )

        mondays = [
            datetime.date(2025, 10, 20),
            datetime.date(2025, 10, 27),
        ]

        self.assertEqual(2, mock_get_week_group.call_count)
        mock_get_week_group.assert_has_calls([call(monday) for monday in mondays])

        self.assertEqual(1, mock_create_shifts_for_group.call_count)
        mock_create_shifts_for_group.assert_called_once_with(
            at_date=datetime.date(2025, 10, 20),
            group=week_group_a,
            filter_shift_template_ids={3, 4},
        )

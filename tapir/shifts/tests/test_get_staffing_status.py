import pytest

from tapir.shifts.management.commands.send_shift_watch_mail import get_staffing_status
from tapir.shifts.models import StaffingStatusChoices


@pytest.mark.parametrize(
    "number_of_available_slots, valid_attendances, required_attendances, last_status, expected",
    [
        (5, 2, 3, None, StaffingStatusChoices.UNDERSTAFFED),
        (5, 4, 4, None, StaffingStatusChoices.ALMOST_FULL),
        (5, 5, 5, None, StaffingStatusChoices.FULL),
        (5, 3, 3, StaffingStatusChoices.UNDERSTAFFED, StaffingStatusChoices.ALL_CLEAR),
        (5, 4, 4, StaffingStatusChoices.ALMOST_FULL, None),
        (5, 2, 3, StaffingStatusChoices.UNDERSTAFFED, None),
    ],
)
def test_getStaffingStatus_Parametrized(
    number_of_available_slots,
    valid_attendances,
    required_attendances,
    last_status,
    expected,
):
    result = get_staffing_status(
        number_of_available_slots, valid_attendances, required_attendances, last_status
    )
    assert result == expected

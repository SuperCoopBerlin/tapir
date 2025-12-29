import pytest


from tapir.shifts.models import StaffingStatusChoices
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator


@pytest.mark.parametrize(
    "number_of_available_slots, valid_attendances, required_attendances, last_status, expected",
    [
        (5, 2, 3, None, StaffingStatusChoices.UNDERSTAFFED),
        (5, 4, 4, None, StaffingStatusChoices.ALMOST_FULL),
        (5, 5, 5, None, StaffingStatusChoices.FULL),
        (5, 3, 3, StaffingStatusChoices.UNDERSTAFFED, StaffingStatusChoices.ALL_CLEAR),
        (5, 4, 4, StaffingStatusChoices.ALMOST_FULL, None),
        (5, 2, 3, StaffingStatusChoices.UNDERSTAFFED, None),
        (1, 0, 1, None, StaffingStatusChoices.UNDERSTAFFED),
        (1, 0, 1, StaffingStatusChoices.UNDERSTAFFED, None),
        (1, 0, 0, StaffingStatusChoices.ALMOST_FULL, None),
        (1, 1, 1, StaffingStatusChoices.UNDERSTAFFED, StaffingStatusChoices.FULL),
    ],
)
def test_getStaffingStatus_Parametrized(
    number_of_available_slots,
    valid_attendances,
    required_attendances,
    last_status,
    expected,
):
    result = ShiftWatchCreator.get_staffing_status_if_changed(
        number_of_available_slots, valid_attendances, required_attendances, last_status
    )
    assert result == expected

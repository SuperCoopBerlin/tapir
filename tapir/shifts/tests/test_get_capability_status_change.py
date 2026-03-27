import pytest

from tapir.shifts.models import (
    ShiftSlot,
    SHIFT_USER_CAPABILITY_CHOICES,
    ShiftUserCapability,
)
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.tests.factories import (
    ShiftSlotFactory,
    ShiftFactory,
    ShiftWatchFactory,
)


@pytest.fixture(scope="function")
def set_up_slots(db):
    shift = ShiftFactory.create(nb_slots=0)
    slot_1 = ShiftSlotFactory.create(
        id=1, shift=shift, required_capabilities=[ShiftUserCapability.SHIFT_COORDINATOR]
    )
    slot_2 = ShiftSlotFactory.create(id=2, shift=shift, required_capabilities=[])
    slot_3 = ShiftSlotFactory.create(
        id=3, shift=shift, required_capabilities=[ShiftUserCapability.HANDLING_CHEESE]
    )
    # ShiftWatchFactory.create(shift=shift)
    return {
        "slot_1": slot_1.id,
        "slot_2": slot_2.id,
        "slot_3": slot_3.id,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "this_valid_slot_ids, last_valid_slot_ids, watched_capabilities, expected_notifications",
    [
        ([], [], [], []),
        (
            [1, 2],
            [2],
            [ShiftUserCapability.SHIFT_COORDINATOR],
            [f"Member with capability added: {ShiftUserCapability.SHIFT_COORDINATOR}"],
        ),
        (
            [2],
            [1, 2],
            [ShiftUserCapability.SHIFT_COORDINATOR],
            [
                f"Member with capability unregistered: {ShiftUserCapability.SHIFT_COORDINATOR}"
            ],
        ),
        ([1, 2], [1, 2], [{ShiftUserCapability.SHIFT_COORDINATOR}], []),
        (
            [3],
            [2],
            [ShiftUserCapability.HANDLING_CHEESE],
            [f"Member with capability added: {ShiftUserCapability.HANDLING_CHEESE}"],
        ),
        (
            [3],
            [2],
            [ShiftUserCapability.SHIFT_COORDINATOR],
            [],
        ),  # only should trigger when HANDLING_CHEESE is watched
        (
            [2],
            [3],
            [ShiftUserCapability.HANDLING_CHEESE],
            [
                f"Member with capability unregistered: {ShiftUserCapability.HANDLING_CHEESE}"
            ],
        ),
    ],
)
def test_get_capability_status_changes(
    set_up_slots,
    this_valid_slot_ids,
    last_valid_slot_ids,
    watched_capabilities,
    expected_notifications,
):
    print(
        ShiftSlot.objects.filter(id__in=this_valid_slot_ids).values_list(
            "required_capabilities", flat=True
        )
    )
    print(
        ShiftSlot.objects.filter(id__in=last_valid_slot_ids).values_list(
            "required_capabilities", flat=True
        )
    )
    result = ShiftWatchCreator.get_capability_status_changes(
        this_valid_slot_ids, last_valid_slot_ids, watched_capabilities
    )
    assert result == expected_notifications

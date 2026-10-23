import pytest

from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.tests.factories import (
    CapabilityFactory,
    ShiftFactory,
    ShiftSlotFactory,
)


@pytest.fixture(scope="function")
def set_up_slots(db):
    shift = ShiftFactory.create(nb_slots=0)

    coordinator_cap = CapabilityFactory.create()
    coordinator_cap.capabilitytranslation_set.create(
        name="SHIFT_COORDINATOR", language="en"
    )
    cheese_cap = CapabilityFactory.create()
    cheese_cap.capabilitytranslation_set.create(name="HANDLING_CHEESE", language="en")

    slot_1 = ShiftSlotFactory.create(id=1, shift=shift)
    slot_1.required_capabilities.set([coordinator_cap])
    slot_2 = ShiftSlotFactory.create(id=2, shift=shift)
    slot_2.required_capabilities.set([])
    slot_3 = ShiftSlotFactory.create(id=3, shift=shift)
    slot_3.required_capabilities.set([cheese_cap])

    return {
        "slot_1": slot_1.id,
        "slot_2": slot_2.id,
        "slot_3": slot_3.id,
        "coordinator_cap": coordinator_cap,
        "cheese_cap": cheese_cap,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "this_valid_slot_ids, last_valid_slot_ids, watched_capability_keys, expected_notifications",
    [
        ([], [], [], []),
        (
            [1, 2],
            [2],
            ["coordinator_cap"],
            ["Member with capability added: SHIFT_COORDINATOR"],
        ),
        (
            [2],
            [1, 2],
            ["coordinator_cap"],
            ["Member with capability unregistered: SHIFT_COORDINATOR"],
        ),
        ([1, 2], [1, 2], ["coordinator_cap"], []),
        ([3], [2], ["cheese_cap"], ["Member with capability added: HANDLING_CHEESE"]),
        ([3], [2], ["coordinator_cap"], []),
        (
            [2],
            [3],
            ["cheese_cap"],
            ["Member with capability unregistered: HANDLING_CHEESE"],
        ),
    ],
)
def test_get_capability_status_changes(
    set_up_slots,
    this_valid_slot_ids,
    last_valid_slot_ids,
    watched_capability_keys,
    expected_notifications,
):
    watched_capabilities = [set_up_slots[key] for key in watched_capability_keys]

    result = ShiftWatchCreator.get_capability_status_changes(
        this_valid_slot_ids, last_valid_slot_ids, watched_capabilities
    )
    assert result == expected_notifications

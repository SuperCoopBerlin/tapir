import pytest

from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.tests.factories import (
    CapabilityFactory,
    CapabilityTranslationFactory,
    ShiftFactory,
    ShiftSlotFactory,
)


@pytest.fixture(scope="function")
def set_up_slots(db):
    shift = ShiftFactory.create(nb_slots=0)

    capability_1 = CapabilityFactory.create()
    CapabilityTranslationFactory.create(
        capability=capability_1, name="CAPABILITY_1", language="en"
    )
    capability_2 = CapabilityFactory.create()
    CapabilityTranslationFactory.create(
        capability=capability_2, name="CAPABILITY_2", language="en"
    )

    slot_1 = ShiftSlotFactory.create(id=1, shift=shift)
    slot_1.required_capabilities.set([capability_1])
    slot_2 = ShiftSlotFactory.create(id=2, shift=shift)
    slot_2.required_capabilities.set([])
    slot_3 = ShiftSlotFactory.create(id=3, shift=shift)
    slot_3.required_capabilities.set([capability_2])

    return {
        "slot_1": slot_1.id,
        "slot_2": slot_2.id,
        "slot_3": slot_3.id,
        "coordinator_cap": capability_1,
        "cheese_cap": capability_2,
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
            ["Member with capability added: CAPABILITY_1"],
        ),
        (
            [2],
            [1, 2],
            ["coordinator_cap"],
            ["Member with capability unregistered: CAPABILITY_1"],
        ),
        ([1, 2], [1, 2], ["coordinator_cap"], []),
        ([3], [2], ["cheese_cap"], ["Member with capability added: CAPABILITY_2"]),
        ([3], [2], ["coordinator_cap"], []),
        (
            [2],
            [3],
            ["cheese_cap"],
            ["Member with capability unregistered: CAPABILITY_2"],
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

import datetime

import pytest
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftWatch
from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.utils import get_current_shiftwatch


@pytest.mark.django_db
def test_get_current_shiftwatch_within_timeframe():
    # to be true, the delta needs to be greater than the now + shift-start-time
    shift = ShiftFactory.create(start_time=timezone.now() + datetime.timedelta(days=1))

    # Create a ShiftWatch instance with a notification timedelta that includes the shift
    shift_watch = ShiftWatch.objects.create(
        shift=shift,
        user=TapirUserFactory.create(),
        notification_timedelta=datetime.timedelta(days=2),
    )

    # Call the function
    current_shiftwatches = get_current_shiftwatch()

    # Assert that the ShiftWatch instance is returned
    assert current_shiftwatches.count() == 1
    assert current_shiftwatches.first() == shift_watch


# TODO testen dass ein user nicht zweimal über die gleiche Schicht benachrichtigt wird

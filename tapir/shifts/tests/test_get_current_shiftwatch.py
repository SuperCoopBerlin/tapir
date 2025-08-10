import datetime

import pytest
from unittest.mock import patch
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.core.services.send_mail_service import SendMailService
from tapir.shifts.models import ShiftWatch
from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.utils import get_current_shiftwatch
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftWatch(TapirFactoryTestBase):
    @pytest.mark.django_db
    def test_getCurrentShiftwatch_withinTimeframe_returnsTrue(self):
        shift = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=1)
        )
        shift_watch = ShiftWatch.objects.create(
            shift=shift,
            user=TapirUserFactory.create(),
            notification_timedelta=datetime.timedelta(days=2),
        )
        current_shiftwatches = get_current_shiftwatch()
        assert current_shiftwatches.count() == 1
        assert current_shiftwatches.first() == shift_watch

import datetime

from django.core import mail

from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.shifts.models import ShiftAccountEntry
from tapir.shifts.tests.factories import ShiftFactory
from tapir.shifts.tests.utils import register_user_to_shift
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestRegisterUserToShiftSlotView(TapirFactoryTestBase):
    def setUp(self) -> None:
        mock_timezone_now(test=self, now=datetime.datetime(year=1997, month=9, day=13))

        self.user = self.login_as_normal_user()
        ShareOwnership.objects.update(
            start_date=datetime.date(year=1997, month=1, day=1)
        )
        ShareOwner.objects.update(is_investing=False)
        self.shift = ShiftFactory.create(
            start_time=datetime.datetime(
                year=1997, month=9, day=15, tzinfo=datetime.UTC
            )
        )
        ShiftAccountEntry.objects.create(
            user=self.user,
            value=-4,
            date=datetime.datetime(year=1995, month=1, day=1, tzinfo=datetime.UTC),
        )

    def test_post_memberRegistersToShiftInTheNearFutureAndIsFrozen_memberIsUnfrozen(
        self,
    ):
        shift_user_data = self.user.shift_user_data
        shift_user_data.is_frozen = True
        shift_user_data.save()
        self.shift.start_time = datetime.datetime(
            year=1997, month=9, day=15, tzinfo=datetime.UTC
        )
        self.shift.save()

        register_user_to_shift(client=self.client, shift=self.shift, user=self.user)

        shift_user_data.refresh_from_db()
        self.assertFalse(shift_user_data.is_frozen)

    def test_post_memberRegistersToShiftInTheFarFutureAndIsFrozen_doNothing(self):
        shift_user_data = self.user.shift_user_data
        shift_user_data.is_frozen = True
        shift_user_data.save()
        self.shift.start_time = datetime.datetime(
            year=1997, month=12, day=31, tzinfo=datetime.UTC
        )
        self.shift.save()

        register_user_to_shift(client=self.client, shift=self.shift, user=self.user)

        shift_user_data.refresh_from_db()
        self.assertTrue(shift_user_data.is_frozen)

    def test_post_memberRegistersToShiftInTheNearFutureAndIsNotFrozen_doNothing(self):
        shift_user_data = self.user.shift_user_data
        shift_user_data.is_frozen = False
        shift_user_data.save()
        self.shift.start_time = datetime.datetime(
            year=1997, month=9, day=15, tzinfo=datetime.UTC
        )
        self.shift.save()

        register_user_to_shift(client=self.client, shift=self.shift, user=self.user)

        shift_user_data.refresh_from_db()
        self.assertFalse(shift_user_data.is_frozen)
        self.assertEqual(0, len(mail.outbox))

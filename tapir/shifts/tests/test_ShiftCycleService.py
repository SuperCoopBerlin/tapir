import datetime

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftExemption,
    ShiftTemplate,
    ShiftCycleEntry,
    ShiftUserData,
)
from tapir.shifts.services.shift_cycle_service import ShiftCycleService
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftCycleService(TapirFactoryTestBase):
    FIRST_CYCLE_START_DATE = datetime.date(day=18, month=1, year=2021)
    SECOND_CYCLE_START_DATE = datetime.date(day=15, month=2, year=2021)

    def test_applyCycleStart_default_userBalanceIsCorrect(self):
        user = self.get_user_that_joined_before_first_cycle()

        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            -1,
            "After once cycle, the user's balance should be -1.",
        )

        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            -1,
            "After applying the same cycle, the user's balance should not have changed.",
        )

        ShiftCycleService.apply_cycle_start(self.SECOND_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            -2,
            "After a second, different cycle, the user's balance should be -2.",
        )

    def test_applyCycleStart_userIsInvesting_balanceDoesntChange(self):
        user = self.get_user_that_joined_before_first_cycle()
        user.share_owner.is_investing = True
        user.share_owner.save()
        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "Since that user is investing, they should not loose point at the beginning of the cycle.",
        )

    def test_applyCycleStart_userIsExemptedFromOnceCycle_balanceIsCorrect(self):
        user = self.get_user_that_joined_before_first_cycle()
        ShiftExemption.objects.create(
            start_date=self.FIRST_CYCLE_START_DATE - datetime.timedelta(days=1),
            end_date=self.SECOND_CYCLE_START_DATE - datetime.timedelta(days=1),
            shift_user_data=user.shift_user_data,
        )

        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "The user is exempted from the first cycle, the account balance should be 0.",
        )

        ShiftCycleService.apply_cycle_start(self.SECOND_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            -1,
            "The user is not exempted from the second cycle, the account balance should be -1.",
        )

    def test_applyCycleStart_userIsExemptedFromBothCyclesWithEndDate_balanceIsCorrect(
        self,
    ):
        user = self.get_user_that_joined_before_first_cycle()
        ShiftExemption.objects.create(
            start_date=self.FIRST_CYCLE_START_DATE - datetime.timedelta(days=1),
            end_date=self.SECOND_CYCLE_START_DATE + datetime.timedelta(days=1),
            shift_user_data=user.shift_user_data,
        )

        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        ShiftCycleService.apply_cycle_start(self.SECOND_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "The user is exempted from both cycle, the account balance should be 0.",
        )

    def test_applyCycleStart_userIsExemptedFromBothCyclesWithoutEndDate_balanceIsCorrect(
        self,
    ):
        user = self.get_user_that_joined_before_first_cycle()
        ShiftExemption.objects.create(
            start_date=self.FIRST_CYCLE_START_DATE - datetime.timedelta(days=1),
            end_date=None,
            shift_user_data=user.shift_user_data,
        )

        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        ShiftCycleService.apply_cycle_start(self.SECOND_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "The user is exempted from both cycle, the account balance should be 0.",
        )

    def test_applyCycleStart_userJoinedAfterCycle_balanceIsCorrect(self):
        user = TapirUserFactory.create(
            share_owner__is_investing=False,
            date_joined=self.FIRST_CYCLE_START_DATE + datetime.timedelta(days=7),
        )

        ShiftCycleService.apply_cycle_start(self.FIRST_CYCLE_START_DATE)
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "The user joined the coop after the cycle started, they should not have lost a point.",
        )

    def get_user_that_joined_before_first_cycle(self) -> TapirUser:
        return TapirUserFactory.create(
            share_owner__is_investing=False,
            date_joined=self.FIRST_CYCLE_START_DATE - datetime.timedelta(days=7),
        )

    def test_getNextCycleStartDate_noPreexistingShiftCycleEntry_returnsMondayOfFirstShift(
        self,
    ):
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift_template.create_shift(
            datetime.date(year=2024, month=8, day=15)
        )  # This is a Thursday

        self.assertEqual(
            datetime.date(year=2024, month=8, day=12),
            ShiftCycleService.get_next_cycle_start_date(),
        )

    def test_getNextCycleStartDate_pastShiftCycleEntryExist_returnsLatestEntryPlusCycleDuration(
        self,
    ):
        shift_user_data: ShiftUserData = TapirUserFactory.create().shift_user_data
        ShiftCycleEntry.objects.create(
            shift_user_data=shift_user_data,
            cycle_start_date=self.FIRST_CYCLE_START_DATE,
        )
        ShiftCycleEntry.objects.create(
            shift_user_data=shift_user_data,
            cycle_start_date=self.FIRST_CYCLE_START_DATE - datetime.timedelta(days=10),
        )

        self.assertEqual(
            self.SECOND_CYCLE_START_DATE,
            ShiftCycleService.get_next_cycle_start_date(),
        )

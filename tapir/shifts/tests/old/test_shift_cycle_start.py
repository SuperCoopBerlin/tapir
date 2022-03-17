import datetime

from tapir.accounts.models import TapirUser
from tapir.shifts.models import ShiftExemption, ShiftCycleEntry
from tapir.utils.tests_utils import TAPIR_SELENIUM_BASE_FIXTURES, TapirSeleniumTestBase


class TestShiftCycleStart(TapirSeleniumTestBase):
    fixtures = TAPIR_SELENIUM_BASE_FIXTURES + ["test_shift_cycle_start.json"]

    def test_shift_cycle_start(self):
        user_one: TapirUser = TapirUser.objects.get(username="user.one")
        user_two: TapirUser = TapirUser.objects.get(username="user.two")
        user_three: TapirUser = TapirUser.objects.get(username="user.three")
        user_four: TapirUser = TapirUser.objects.get(username="user.four")
        user_five: TapirUser = TapirUser.objects.get(username="user.five")

        ShiftExemption.objects.create(
            shift_user_data=user_one.shift_user_data,
            start_date=datetime.date(day=15, month=1, year=2021),
            end_date=datetime.date(day=28, month=2, year=2021),
            description="User one is exempted for both cycles",
        )
        ShiftExemption.objects.create(
            shift_user_data=user_two.shift_user_data,
            start_date=datetime.date(day=15, month=1, year=2021),
            end_date=datetime.date(day=31, month=1, year=2021),
            description="User two is exempted for the first cycle",
        )
        ShiftExemption.objects.create(
            shift_user_data=user_three.shift_user_data,
            start_date=datetime.date(day=1, month=12, year=2020),
            end_date=datetime.date(day=31, month=12, year=2020),
            description="User three has an exemption in the past",
        )
        ShiftExemption.objects.create(
            shift_user_data=user_four.shift_user_data,
            start_date=datetime.date(day=15, month=1, year=2021),
            description="User four has an exemption with no end date",
        )

        first_cycle_start_date = datetime.date(day=18, month=1, year=2021)
        second_cycle_start_date = datetime.date(day=15, month=2, year=2021)

        # Apply both starts twice to test that the function is repeatable
        ShiftCycleEntry.apply_cycle_start(first_cycle_start_date)
        ShiftCycleEntry.apply_cycle_start(first_cycle_start_date)
        ShiftCycleEntry.apply_cycle_start(second_cycle_start_date)
        ShiftCycleEntry.apply_cycle_start(second_cycle_start_date)

        self.assertEqual(
            user_one.shift_user_data.get_account_balance(),
            0,
            "user_one is exempted from both cycles, his account balance should be 0",
        )
        self.assertEqual(
            user_two.shift_user_data.get_account_balance(),
            -1,
            "user_two is exempted from only one cycle, his account balance should be -1",
        )
        self.assertEqual(
            user_three.shift_user_data.get_account_balance(),
            -2,
            "user_three is not exempted from any cycle, his account balance should be -2",
        )
        self.assertEqual(
            user_four.shift_user_data.get_account_balance(),
            0,
            "user_four has an exemption with no end date that covers both cycles, it's balance should be 0",
        )
        self.assertEqual(
            user_five.shift_user_data.get_account_balance(),
            0,
            "user_five is an investing member, they are not required to do shifts, their balance should be 0",
        )

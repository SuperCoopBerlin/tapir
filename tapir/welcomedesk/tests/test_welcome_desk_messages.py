import datetime

from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import (
    ShiftAttendanceMode,
    ShiftAccountEntry,
    ShiftAttendanceTemplate,
    ShiftExemption,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestWelcomeDeskMessages(TapirFactoryTestBase):
    class Messages:
        CAN_SHOP = "welcome_desk_can_shop"
        NO_ACCOUNT = "welcome_desk_no_account"
        SHIFT_BALANCE_NOT_OK = "welcome_desk_shift_balance_not_ok"
        IS_INVESTING = "welcome_desk_is_investing"
        NO_ABCD_SHIFT = "welcome_desk_no_abcd_shift"
        NO_WELCOME_SESSION = "welcome_desk_no_welcome_session"

    MESSAGES = [
        Messages.CAN_SHOP,
        Messages.NO_ACCOUNT,
        Messages.SHIFT_BALANCE_NOT_OK,
        Messages.IS_INVESTING,
        Messages.NO_ABCD_SHIFT,
        Messages.NO_WELCOME_SESSION,
    ]

    def test_no_warnings(self):
        self.check_alerts(
            self.get_no_warnings_user().share_owner, [self.Messages.CAN_SHOP]
        )

    def test_no_account(self):
        self.check_alerts(
            ShareOwnerFactory.create(attended_welcome_session=True, is_investing=False),
            [self.Messages.NO_ACCOUNT],
        )

    def test_shift_balance_not_ok(self):
        user = self.get_no_warnings_user()
        ShiftAccountEntry.objects.create(
            user=user, value=-5, date=datetime.datetime.now()
        )
        self.check_alerts(user.share_owner, [self.Messages.SHIFT_BALANCE_NOT_OK])

    def test_is_investing(self):
        user = self.get_no_warnings_user()
        user.share_owner.is_investing = True
        user.share_owner.save()
        self.check_alerts(user.share_owner, [self.Messages.IS_INVESTING])

    def test_no_abcd_shift(self):
        user = self.get_no_warnings_user()
        user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        user.shift_user_data.save()
        self.assertFalse(
            user.shift_user_data.is_currently_exempted_from_shifts(),
            "We assume that the user is not currently exempted.",
        )
        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(user=user).exists(),
            "We assume that the create user is not registered to any ABCD shift",
        )
        self.check_alerts(
            user.share_owner, [self.Messages.NO_ABCD_SHIFT, self.Messages.CAN_SHOP]
        )

    def test_no_abcd_shift_but_exempted(self):
        user = self.get_no_warnings_user()
        user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        user.shift_user_data.save()
        ShiftExemption.objects.create(
            shift_user_data=user.shift_user_data,
            start_date=datetime.date.today() - datetime.timedelta(days=3),
        )
        self.assertTrue(
            user.shift_user_data.is_currently_exempted_from_shifts(),
            "The user should be exempted.",
        )
        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(user=user).exists(),
            "We assume that the create user is not registered to any ABCD shift",
        )
        self.check_alerts(user.share_owner, [self.Messages.CAN_SHOP])

    def test_no_welcome_session(self):
        user = self.get_no_warnings_user()
        user.share_owner.attended_welcome_session = False
        user.share_owner.save()
        self.check_alerts(
            user.share_owner, [self.Messages.NO_WELCOME_SESSION, self.Messages.CAN_SHOP]
        )

    def check_alerts(self, share_owner: ShareOwner, expected_messages):
        self.login_as_member_office_user()
        response = self.client.get(
            reverse("welcomedesk:welcome_desk_share_owner", args=[share_owner.id])
        )
        response_content = response.content.decode()
        for message in self.MESSAGES:
            if message in expected_messages:
                self.assertIn(
                    message,
                    response_content,
                    f"Message {message} should be showing for user {share_owner.get_info().get_display_name()}",
                )
            else:
                self.assertNotIn(
                    message,
                    response_content,
                    f"Message {message} should not be showing for user {share_owner.get_info().get_display_name()}",
                )

    @staticmethod
    def get_no_warnings_user() -> TapirUser:
        user = TapirUserFactory.create(
            share_owner__is_investing=False, share_owner__attended_welcome_session=True
        )
        user.shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        user.shift_user_data.save()
        return user

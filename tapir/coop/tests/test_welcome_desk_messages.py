import datetime

from django.test import tag
from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftAccountEntry
from tapir.utils.tests_utils import TapirSeleniumTestBase


class TestWelcomeDeskMessages(TapirSeleniumTestBase):
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

    @tag("selenium")
    def test_welcome_desk_messages(self):
        self.login_as_admin()

        roberto = TapirUser.objects.get(username="roberto.cortes")
        all_ok_member = roberto.share_owner
        self.check_alerts(all_ok_member.id, [self.Messages.CAN_SHOP])

        ShiftAccountEntry.objects.create(
            user=roberto, value=-5, date=datetime.datetime.now()
        )
        self.check_alerts(all_ok_member.id, [self.Messages.SHIFT_BALANCE_NOT_OK])

        investing_member = ShareOwner.objects.get(
            email="mehmet.menemencioglu@example.com"
        )
        self.check_alerts(
            investing_member.id,
            [self.Messages.IS_INVESTING, self.Messages.NO_ACCOUNT],
        )

        no_welcome_session_member = TapirUser.objects.get(
            username="carmelo.rodriguez"
        ).share_owner
        self.check_alerts(
            no_welcome_session_member.id,
            [self.Messages.CAN_SHOP, self.Messages.NO_WELCOME_SESSION],
        )

        no_abcd_shift_member = TapirUser.objects.get(
            username="margarethe.dohmen"
        ).share_owner
        self.check_alerts(
            no_abcd_shift_member.id,
            [self.Messages.CAN_SHOP, self.Messages.NO_ABCD_SHIFT],
        )

    def check_alerts(self, share_owner_id, expected_messages):
        self.reset_page()
        self.selenium.get(
            self.live_server_url
            + reverse("coop:welcome_desk_share_owner", args=[share_owner_id])
        )
        for message in self.MESSAGES:
            found = len(self.selenium.find_elements_by_id(message))
            if message in expected_messages:
                self.assertEqual(
                    found,
                    1,
                    f"Message {message} should be showing for user {ShareOwner.objects.get(id=share_owner_id).get_info().get_display_name()}",
                )
            else:
                self.assertEqual(
                    found,
                    0,
                    f"Message {message} should not be showing for user {ShareOwner.objects.get(id=share_owner_id).get_info().get_display_name()}",
                )

    def reset_page(self):
        self.selenium.get(self.live_server_url + reverse("coop:welcome_desk_search"))
        self.wait_until_element_present_by_id("welcome_desk_table")

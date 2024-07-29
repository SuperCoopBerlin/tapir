import datetime
from django.urls import reverse

from tapir.coop.tests.factories import (
    MembershipResignationFactory,
    ShareOwnerFactory,
    MembershipPauseFactory,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateMembershipResignation(TapirFactoryTestBase):
    def test_membershipResignation_created_isTrue(self):
        self.login_as_member_office_user()
        resigned_member = MembershipResignationFactory.create()

        response = self.client.post(
            reverse(
                "coop/resign_member/new",
                {
                    "share_owner": resigned_member,
                    "cancellation_date": datetime.now(),
                    "pay_out_day": datetime.now() + datetime(day=31, month=12, years=3),
                    "cancellation_reason": resigned_member.cancellation_reason,
                    "resignation_type": resigned_member.resignation_type,
                    "transferring_shares_to": resigned_member.transferring_shares_to,
                    "paid_out": resigned_member.paid_out,
                },
                follow=True,
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_membershippause_deletion(self):
        share_owner = ShareOwnerFactory.create()
        membershippause = MembershipPauseFactory.create(share_owner=share_owner)
        MembershipResignationFactory.create(share_owner=share_owner)

        self.assertNone(
            membershippause(share_owner=share_owner), "Membership pause test failed."
        )

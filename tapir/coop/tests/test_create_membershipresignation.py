from datetime import datetime
from dateutil.relativedelta import relativedelta
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
        resignation = MembershipResignationFactory.build()

        response = self.client.post(
            reverse("coop:resign_new_membership"),
            {
                "share_owner": resignation.share_owner,
                "cancellation_date": datetime.now(),
                "pay_out_day": datetime.now()
                + relativedelta(day=31, month=12, years=3),
                "cancellation_reason": resignation.cancellation_reason,
                "resignation_type": resignation.resignation_type,
                "transferring_shares_to": resignation.transferring_shares_to,
                "paid_out": resignation.paid_out,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

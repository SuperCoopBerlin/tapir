from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.tests.factories import (
    MembershipResignationFactory,
    ShareOwnerFactory,
)
from tapir.core.models import FeatureFlag
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateMembershipResignation(TapirFactoryTestBase):
    def test_membershipResignation_created_isTrue(self):
        self.login_as_member_office_user()
        resignation = MembershipResignationFactory.build()
        resignation_flag = FeatureFlag.objects.create(
            flag_name=feature_flag_membership_resignation, flag_value=True
        )
        resignation_flag.save()

        response = self.client.post(
            reverse("coop:resign_new_membership"),
            {
                "share_owner": ShareOwnerFactory.create().id,
                "cancellation_date": datetime.now(),
                "pay_out_day": datetime.now()
                + relativedelta(years=+3, day=31, month=12),
                "cancellation_reason": resignation.cancellation_reason,
                "resignation_type": resignation.resignation_type,
                "transferring_shares_to": ShareOwnerFactory.create().id,
                "paid_out": resignation.paid_out,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

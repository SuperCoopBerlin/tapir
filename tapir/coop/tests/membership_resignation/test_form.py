import datetime
from http import HTTPStatus
from django.urls import reverse

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)

from icecream import ic

from tapir.coop.models import MembershipResignation
from tapir.coop.forms import MembershipResignationForm
from tapir.coop.tests.factories import MembershipResignationFactory, ShareOwnerFactory


class TestMembershipResignationForm(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_form_valid(self):
        member_to_resign = ShareOwnerFactory.create()

        data = {
            "share_owner": member_to_resign.id,
            "cancellation_reason": "Test resignation",
            "cancellation_date": self.TODAY,
            "resignation_type": MembershipResignation.ResignationType.GIFT_TO_COOP,
        }
        form = MembershipResignationForm(data=data)
        self.assertTrue(form.is_valid())
        # resignation = MembershipResignationFactory.create()
        # data = {
        #     "share_owner": ic(resignation.share_owner),
        #     "cancellation_reason": ic(resignation.cancellation_reason),
        #     "cancellation_date": ic(resignation.cancellation_date),
        #     "paid_out": ic(resignation.paid_out),
        # }
        # form = MembershipResignationForm(data=data)
        # self.assertTrue(form.is_valid())

    def test_form_no_data(self):
        MembershipResignationFactory()
        form = MembershipResignationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 6)

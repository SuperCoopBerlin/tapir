from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.models import ShareOwnership
from tapir.coop.tests.factories import DraftUserFactory
from tapir.coop.views import create_share_owner_and_shares_from_draft_user
from tapir.utils.tests_utils import TapirFactoryTestBase


class PaidShareTests(TapirFactoryTestBase):
    def test_create_share_owner_with_unpaid_shares(self):
        draft_user = DraftUserFactory.create(paid_shares=False)
        share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
        for ownership in ShareOwnership.objects.filter(share_owner=share_owner):
            self.assertEqual(
                0,
                ownership.amount_paid,
                "The DraftUser was marked as not having paid, the shares should have 0 as amount_paid",
            )

    def test_create_share_owner_with_paid_shares(self):
        draft_user = DraftUserFactory.create(paid_shares=True)
        share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
        for ownership in ShareOwnership.objects.filter(share_owner=share_owner):
            self.assertEqual(
                COOP_SHARE_PRICE,
                ownership.amount_paid,
                "The DraftUser was marked as having paid, the shares should also be paid.",
            )

from tapir.coop.models import DraftUser, ShareOwnership, COOP_SHARE_PRICE
from tapir.coop.views import create_share_owner_and_shares_from_draft_user
from tapir.utils.tests_utils import LdapEnabledTestCase


class PaidShareTests(LdapEnabledTestCase):
    def test_create_share_owner_with_unpaid_shares(self):
        draft_user = DraftUser.objects.create()
        draft_user.paid_shares = False
        draft_user.num_shares = 3
        share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
        for ownership in ShareOwnership.objects.filter(owner=share_owner):
            self.assertEqual(0, ownership.amount_paid)

    def test_create_share_owner_with_paid_shares(self):
        draft_user = DraftUser.objects.create()
        draft_user.paid_shares = True
        draft_user.num_shares = 5
        share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
        for ownership in ShareOwnership.objects.filter(owner=share_owner):
            self.assertEqual(COOP_SHARE_PRICE, ownership.amount_paid)

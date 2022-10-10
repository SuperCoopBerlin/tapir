from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import (
    IncomingPayment,
    ShareOwner,
    ShareOwnership,
)
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShareOwnerPayments(TapirFactoryTestBase):
    def test_share_owner_get_total_expected_payment(self):
        member: ShareOwner = ShareOwnerFactory.create(nb_shares=3)
        self.assertEqual(
            member.get_total_expected_payment(),
            310,
            "Total expected should be 3x share price + entry fee, or 3x100+10",
        )
        ShareOwnership.objects.create(
            share_owner=member, start_date=timezone.now().date()
        )
        self.assertEqual(member.get_total_expected_payment(), 410)
        ShareOwnership.objects.create(
            share_owner=ShareOwnerFactory.create(), start_date=timezone.now().date()
        )
        self.assertEqual(member.get_total_expected_payment(), 410)

    def test_share_owner_get_currently_paid_amount(self):
        member: ShareOwner = ShareOwnerFactory.create(nb_shares=1)
        self.assertEqual(member.get_currently_paid_amount(), 0)

        self.create_incoming_payment(member, 55)
        self.assertEqual(member.get_currently_paid_amount(), 55)

        self.create_incoming_payment(member, 66)
        self.assertEqual(member.get_currently_paid_amount(), 121)

        self.create_incoming_payment(ShareOwnerFactory.create(), 100)
        self.assertEqual(member.get_currently_paid_amount(), 121)

    @staticmethod
    def create_incoming_payment(member: ShareOwner, amount) -> IncomingPayment:
        return IncomingPayment.objects.create(
            paying_member=member,
            credited_member=member,
            amount=amount,
            payment_date=timezone.now().date(),
            creation_date=timezone.now().date(),
            created_by=TapirUserFactory.create(is_in_member_office=True),
        )

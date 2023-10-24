import datetime
from abc import ABC, abstractmethod

from tapir.coop.models import (
    MEMBER_STATUS_CHOICES,
)
from tapir.coop.models import (
    ShareOwner,
    MemberStatus,
    ShareOwnership,
)
from tapir.coop.tests.factories import ShareOwnerFactory, MembershipPauseFactory
from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.utils.tests_utils import mock_timezone_now


class ShareOwnerStatusBaseTestClass(ABC):
    # since we want to make sure that ShareOwnerQuerySet.with_status() and ShareOwner.get_member_status()
    # give the same results, we use the same range of tests

    @abstractmethod
    def assertMemberStatus(self, member, expected_status):
        pass

    def test_memberHasNoShares_returnsSold(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=0, is_investing=False
        )
        self.assertMemberStatus(share_owner, MemberStatus.SOLD)

    def test_hasPastShares_returnsSold(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=False
        )
        share: ShareOwnership = share_owner.share_ownerships.first()
        share.start_date = datetime.date(year=2020, month=1, day=1)
        share.end_date = datetime.date(year=2022, month=1, day=1)
        share.save()
        mock_timezone_now(self, datetime.datetime(year=2023, month=1, day=1))
        self.assertMemberStatus(share_owner, MemberStatus.SOLD)

    def test_hasFutureShares_returnsSold(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=False
        )
        share: ShareOwnership = share_owner.share_ownerships.first()
        share.start_date = datetime.date(year=2024, month=1, day=1)
        share.save()
        mock_timezone_now(self, datetime.datetime(year=2023, month=1, day=1))
        self.assertMemberStatus(share_owner, MemberStatus.SOLD)

    def test_hasNoSharesAndIsInvesting_returnsSold(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=0, is_investing=True
        )
        self.assertMemberStatus(share_owner, MemberStatus.SOLD)

    def test_isInvesting_returnsInvesting(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=True
        )
        self.assertMemberStatus(share_owner, MemberStatus.INVESTING)

    def test_isInvestingAndPaused_returnsInvesting(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=True
        )
        MembershipPauseFactory.create(
            share_owner=share_owner,
            start_date=datetime.date(year=2022, month=1, day=1),
            end_date=datetime.date(year=2024, month=1, day=1),
        )
        mock_timezone_now(self, datetime.datetime(year=2023, month=1, day=1))
        self.assertMemberStatus(share_owner, MemberStatus.INVESTING)

    def test_isPaused_returnsPaused(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=False
        )
        MembershipPauseFactory.create(
            share_owner=share_owner,
            start_date=datetime.date(year=2022, month=1, day=1),
            end_date=datetime.date(year=2024, month=1, day=1),
        )
        mock_timezone_now(self, datetime.datetime(year=2023, month=1, day=1))
        self.assertMemberStatus(share_owner, MemberStatus.PAUSED)

    def test_hasInvactivePause_returnsActive(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=False
        )
        MembershipPauseFactory.create(
            share_owner=share_owner,
            start_date=datetime.date(year=2020, month=1, day=1),
            end_date=datetime.date(year=2022, month=1, day=1),
        )
        mock_timezone_now(self, datetime.datetime(year=2023, month=1, day=1))
        self.assertMemberStatus(share_owner, MemberStatus.ACTIVE)

    def test_default_returnsActive(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(
            nb_shares=1, is_investing=False
        )
        self.assertMemberStatus(share_owner, MemberStatus.ACTIVE)


class TestShareOwnerGetMemberStatus(
    ShareOwnerStatusBaseTestClass, TapirFactoryTestBase
):
    def assertMemberStatus(self, member: ShareOwner, expected_status: str):
        self.assertEqual(member.get_member_status(), expected_status)


class TestShareOwnerQuerySetWithStatus(
    ShareOwnerStatusBaseTestClass, TapirFactoryTestBase
):
    def assertMemberStatus(self, member: ShareOwner, expected_status: str):
        for status in MEMBER_STATUS_CHOICES:
            queryset = ShareOwner.objects.with_status(status[0])
            if status[0] == expected_status:
                self.assertEqual(1, queryset.count())
                self.assertIn(member, queryset)
            else:
                self.assertEqual(0, queryset.count())

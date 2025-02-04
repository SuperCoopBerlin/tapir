import datetime

from django.utils import timezone

from tapir.coop.models import MemberStatus, MembershipPause
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.services.data_providers.data_provider_total_members import (
    DataProviderTotalMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderActiveMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberStatusSold_notIncluded(self):
        member_sold = ShareOwnerFactory.create(nb_shares=0)
        self.assertEqual(
            MemberStatus.SOLD, member_sold.get_member_status(self.REFERENCE_TIME)
        )

        queryset = DataProviderTotalMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberStatusInvesting_included(self):
        member_investing = ShareOwnerFactory.create(is_investing=True)
        self.assertEqual(
            MemberStatus.INVESTING,
            member_investing.get_member_status(self.REFERENCE_TIME),
        )

        queryset = DataProviderTotalMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(member_investing, queryset)

    def test_getQueryset_memberStatusPaused_included(self):
        member_paused = ShareOwnerFactory.create(is_investing=False)
        MembershipPause.objects.create(
            share_owner=member_paused,
            description="Test",
            start_date=self.REFERENCE_TIME.date(),
        )
        self.assertEqual(
            MemberStatus.PAUSED,
            member_paused.get_member_status(self.REFERENCE_TIME),
        )

        queryset = DataProviderTotalMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(member_paused, queryset)

    def test_getQueryset_memberStatusActive_included(self):
        member_active = ShareOwnerFactory.create(is_investing=False)
        self.assertEqual(
            MemberStatus.ACTIVE,
            member_active.get_member_status(self.REFERENCE_TIME),
        )

        queryset = DataProviderTotalMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(member_active, queryset)

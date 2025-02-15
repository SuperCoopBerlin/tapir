import datetime

from django.utils import timezone

from tapir.coop.models import MembershipPause
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.services.data_providers.data_provider_paused_members import (
    DataProviderPausedMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderPausedMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberIsNotPaused_notIncluded(self):
        ShareOwnerFactory.create()

        queryset = DataProviderPausedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsPaused_included(self):
        share_owner = ShareOwnerFactory.create(is_investing=False)
        MembershipPause.objects.create(
            share_owner=share_owner,
            description="Test",
            start_date=self.REFERENCE_TIME.date(),
        )

        queryset = DataProviderPausedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(share_owner, queryset)

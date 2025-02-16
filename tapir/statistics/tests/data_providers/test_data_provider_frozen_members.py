import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftUserData
from tapir.statistics.services.data_providers.data_provider_frozen_members import (
    DataProviderFrozenMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderFrozenMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberIsFrozenButIsNotActive_notIncluded(self):
        TapirUserFactory.create(share_owner__is_investing=True)
        ShiftUserData.objects.update(is_frozen=True)

        queryset = DataProviderFrozenMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsActiveButIsNotFrozen_notIncluded(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShiftUserData.objects.update(is_frozen=False)

        queryset = DataProviderFrozenMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsActiveAndFrozen_included(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShiftUserData.objects.update(is_frozen=True)

        queryset = DataProviderFrozenMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

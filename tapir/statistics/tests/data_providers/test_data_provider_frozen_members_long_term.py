import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwnership
from tapir.shifts.models import ShiftUserData, UpdateShiftUserDataLogEntry
from tapir.statistics.services.data_providers.data_provider_frozen_members_long_term import (
    DataProviderFrozenMembersLongTerm,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestDataProviderLongTermFrozenMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_getQueryset_memberIsNotFrozen_notIncluded(self):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=False)

        queryset = DataProviderFrozenMembersLongTerm.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsFrozenSinceNotLongEnough_notIncluded(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": False},
            new_values={"is_frozen": True},
        )
        log_entry.created_date = self.REFERENCE_TIME - datetime.timedelta(days=150)
        log_entry.save()

        queryset = DataProviderFrozenMembersLongTerm.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberIsFrozenSinceLongEnough_included(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": False},
            new_values={"is_frozen": True},
        )
        log_entry.created_date = self.REFERENCE_TIME - datetime.timedelta(days=190)
        log_entry.save()

        queryset = DataProviderFrozenMembersLongTerm.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

    def test_getQueryset_memberIsFrozenAndHasNoLogs_included(self):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        queryset = DataProviderFrozenMembersLongTerm.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

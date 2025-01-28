import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwnership
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.views.fancy_graph.number_of_active_members_with_account_view import (
    NumberOfActiveMembersWithAccountAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfActiveMembersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=7, day=2, hour=18)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=4, day=8, hour=10)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def create_test_user(self, is_investing=False, date_joined=None):
        if date_joined is None:
            date_joined = self.REFERENCE_TIME - datetime.timedelta(days=1)

        TapirUserFactory.create(
            share_owner__nb_shares=1,
            share_owner__is_investing=is_investing,
            date_joined=date_joined,
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

    def test_calculateDatapoint_memberIsNotActive_notCounted(self):
        self.create_test_user(is_investing=True)

        result = NumberOfActiveMembersWithAccountAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberHasNoAccount_notCounted(self):
        ShareOwnerFactory.create(nb_shares=1, is_investing=False)
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

        result = NumberOfActiveMembersWithAccountAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberCreatedAccountAfterDate_notCounted(self):
        self.create_test_user(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )

        result = NumberOfActiveMembersWithAccountAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberCreatedAccountBeforeDate_counted(self):
        self.create_test_user(
            date_joined=self.REFERENCE_TIME - datetime.timedelta(days=1)
        )

        result = NumberOfActiveMembersWithAccountAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

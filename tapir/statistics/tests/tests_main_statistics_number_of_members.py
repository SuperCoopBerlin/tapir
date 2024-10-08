import datetime

from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.views import MemberCountEvolutionJsonView
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestMainStatisticsViewNumberOfMembers(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=9, day=1, hour=12)

    def test_getNumberOfMembersAtDate(self):
        mock_timezone_now(self, self.NOW)

        # share is expired
        self.create_share_owner_with_share_validity_dates(
            start_date=datetime.date(year=2023, month=1, day=1),
            end_date=datetime.date(year=2023, month=5, day=1),
        )

        # share is valid
        self.create_share_owner_with_share_validity_dates(
            start_date=datetime.date(year=2023, month=1, day=1),
            end_date=datetime.date(year=2023, month=12, day=1),
        )

        # share starts in the future
        self.create_share_owner_with_share_validity_dates(
            start_date=datetime.date(year=2023, month=10, day=1),
            end_date=datetime.date(year=2023, month=12, day=1),
        )

        self.assertEqual(
            1, MemberCountEvolutionJsonView.get_number_of_members_at_date(self.NOW)
        )

    @staticmethod
    def create_share_owner_with_share_validity_dates(start_date, end_date):
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=1)
        share_ownership: ShareOwnership = share_owner.share_ownerships.first()
        share_ownership.start_date = start_date
        share_ownership.end_date = end_date
        share_ownership.save()

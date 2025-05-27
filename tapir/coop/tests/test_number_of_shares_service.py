import datetime

from tapir.coop.models import ShareOwner
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestNumberOfSharesService(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=8, day=7, hour=10, minute=7)
    TODAY = NOW.date()

    def setUp(self) -> None:
        mock_timezone_now(self, self.NOW)

    def test_getNumberOfActiveShares_noAnnotation_returnsCorrectNumber(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=2)
        [active_share, inactive_share] = share_owner.share_ownerships.all()

        active_share.start_date = self.TODAY - datetime.timedelta(days=10)
        active_share.end_date = self.TODAY + datetime.timedelta(days=10)
        active_share.save()

        inactive_share.start_date = self.TODAY - datetime.timedelta(days=5)
        inactive_share.end_date = self.TODAY + datetime.timedelta(days=5)
        inactive_share.save()

        self.assertEqual(
            1,
            NumberOfSharesService.get_number_of_active_shares(
                share_owner, self.TODAY + datetime.timedelta(days=7)
            ),
        )

    def test_getNumberOfActiveShares_withAnnotation_returnsCorrectNumber(self):
        share_owner_with_one_active_share: ShareOwner = ShareOwnerFactory.create(
            nb_shares=2
        )
        [
            active_share,
            inactive_share,
        ] = share_owner_with_one_active_share.share_ownerships.all()

        active_share.start_date = self.TODAY - datetime.timedelta(days=10)
        active_share.end_date = self.TODAY + datetime.timedelta(days=10)
        active_share.save()

        inactive_share.start_date = self.TODAY - datetime.timedelta(days=5)
        inactive_share.end_date = self.TODAY + datetime.timedelta(days=5)
        inactive_share.save()

        share_owner_with_three_active_shares: ShareOwner = ShareOwnerFactory.create(
            nb_shares=3
        )
        share_owner_with_three_active_shares.share_ownerships.update(
            start_date=self.TODAY - datetime.timedelta(days=10),
            end_date=self.TODAY + datetime.timedelta(days=10),
        )

        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            ShareOwner.objects.all(), self.TODAY + datetime.timedelta(days=7)
        )

        self.assertEqual(
            1,
            NumberOfSharesService.get_number_of_active_shares(
                share_owners.get(id=share_owner_with_one_active_share.id),
                self.TODAY + datetime.timedelta(days=7),
            ),
        )
        self.assertEqual(
            3,
            NumberOfSharesService.get_number_of_active_shares(
                share_owners.get(id=share_owner_with_three_active_shares.id),
                self.TODAY + datetime.timedelta(days=7),
            ),
        )

    def test_getNumberOfActiveShares_withAnnotation_noExtraDatabaseQuery(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=100)
        share_owner.share_ownerships.update(
            start_date=self.TODAY - datetime.timedelta(days=7), end_date=None
        )

        with self.assertNumQueries(1):
            share_owner = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
                ShareOwner.objects.all()
            ).first()

        with self.assertNumQueries(0):
            number_of_active_shares = NumberOfSharesService.get_number_of_active_shares(
                share_owner
            )

        self.assertEqual(100, number_of_active_shares)

    def test_getNumberOfActiveShares_annotationWithWrongDate_raisesException(self):
        ShareOwnerFactory.create()

        share_owner = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            ShareOwner.objects.all(), self.TODAY
        ).first()

        with self.assertRaises(ValueError):
            NumberOfSharesService.get_number_of_active_shares(
                share_owner, self.TODAY + datetime.timedelta(days=7)
            )

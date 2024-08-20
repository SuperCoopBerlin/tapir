import datetime

from tapir.coop.models import ShareOwner
from tapir.coop.services.MemberInfoService import MemberInfoService
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestMemberInfoService(TapirFactoryTestBase):
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
            MemberInfoService.get_number_of_active_shares(
                share_owner, self.TODAY + datetime.timedelta(days=7)
            ),
        )

    def test_getNumberOfActiveShares_withAnnotation_returnsCorrectNumber(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=2)
        [active_share, inactive_share] = share_owner.share_ownerships.all()

        active_share.start_date = self.TODAY - datetime.timedelta(days=10)
        active_share.end_date = self.TODAY + datetime.timedelta(days=10)
        active_share.save()

        inactive_share.start_date = self.TODAY - datetime.timedelta(days=5)
        inactive_share.end_date = self.TODAY + datetime.timedelta(days=5)
        inactive_share.save()

        share_owner = MemberInfoService.annotate_share_owner_queryset_with_number_of_active_shares(
            ShareOwner.objects.all(), self.TODAY + datetime.timedelta(days=7)
        ).first()

        self.assertEqual(
            1,
            MemberInfoService.get_number_of_active_shares(
                share_owner, self.TODAY + datetime.timedelta(days=7)
            ),
        )

    def test_getNumberOfActiveShares_withAnnotation_noExtraDatabaseQuery(self):
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=100)
        share_owner.share_ownerships.update(
            start_date=self.TODAY - datetime.timedelta(days=7), end_date=None
        )

        with self.assertNumQueries(1):
            share_owner = MemberInfoService.annotate_share_owner_queryset_with_number_of_active_shares(
                ShareOwner.objects.all()
            ).first()

        with self.assertNumQueries(0):
            number_of_active_shares = MemberInfoService.get_number_of_active_shares(
                share_owner
            )

        self.assertEqual(100, number_of_active_shares)

    def test_getNumberOfActiveShares_annotationWithWrongDate_raisesException(self):
        ShareOwnerFactory.create()

        share_owner = MemberInfoService.annotate_share_owner_queryset_with_number_of_active_shares(
            ShareOwner.objects.all(), self.TODAY
        ).first()

        with self.assertRaises(ValueError):
            MemberInfoService.get_number_of_active_shares(
                share_owner, self.TODAY + datetime.timedelta(days=7)
            )

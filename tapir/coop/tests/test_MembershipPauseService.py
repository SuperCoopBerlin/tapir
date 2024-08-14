import datetime

from tapir.coop.models import ShareOwner, MembershipPause
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.coop.tests.factories import ShareOwnerFactory, MembershipPauseFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestMembershipPauseService(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=8, day=7, hour=10, minute=7)
    TODAY = NOW.date()

    def setUp(self) -> None:
        mock_timezone_now(self, self.NOW)

    def test_hasActivePause_noAnnotationAndNoPause_returnsFalse(self):
        share_owner: ShareOwner = ShareOwnerFactory.create()
        self.assertFalse(MembershipPauseService.has_active_pause(share_owner))

    def test_hasActivePause_noAnnotationAndOutdatedPause_returnsFalse(self):
        pause: MembershipPause = MembershipPauseFactory.create(
            start_date=self.TODAY - datetime.timedelta(days=10),
            end_date=self.TODAY - datetime.timedelta(days=5),
        )
        self.assertFalse(
            MembershipPauseService.has_active_pause(pause.share_owner, self.TODAY)
        )

    def test_hasActivePause_noAnnotationAndActivePause_returnsTrue(self):
        pause: MembershipPause = MembershipPauseFactory.create(
            start_date=self.TODAY - datetime.timedelta(days=10),
            end_date=self.TODAY + datetime.timedelta(days=5),
        )
        self.assertTrue(
            MembershipPauseService.has_active_pause(pause.share_owner, self.TODAY)
        )

    def test_hasActivePause_withAnnotationAndNoPause_returnsFalse(self):
        ShareOwnerFactory.create()
        share_owner = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                ShareOwner.objects.all()
            ).first()
        )
        self.assertFalse(MembershipPauseService.has_active_pause(share_owner))

    def test_hasActivePause_withAnnotationAndOutdatedPause_returnsFalse(self):
        MembershipPauseFactory.create(
            start_date=self.TODAY - datetime.timedelta(days=10),
            end_date=self.TODAY - datetime.timedelta(days=5),
        )
        share_owner = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                ShareOwner.objects.all()
            ).first()
        )
        self.assertFalse(
            MembershipPauseService.has_active_pause(share_owner, self.TODAY)
        )

    def test_hasActivePause_withAnnotationAndActivePause_returnsTrue(self):
        MembershipPauseFactory.create(
            start_date=self.TODAY - datetime.timedelta(days=10),
            end_date=self.TODAY + datetime.timedelta(days=5),
        )
        share_owner = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                ShareOwner.objects.all()
            ).first()
        )
        self.assertTrue(
            MembershipPauseService.has_active_pause(share_owner, self.TODAY)
        )

    def test_hasActivePause_withAnnotation_noExtraDatabaseQuery(self):
        MembershipPauseFactory.create(
            start_date=self.TODAY - datetime.timedelta(days=10),
            end_date=self.TODAY + datetime.timedelta(days=5),
        )
        with self.assertNumQueries(1):
            share_owner = MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                ShareOwner.objects.all()
            ).first()

        with self.assertNumQueries(0):
            has_active_pause = MembershipPauseService.has_active_pause(
                share_owner, self.TODAY
            )

        self.assertTrue(has_active_pause)

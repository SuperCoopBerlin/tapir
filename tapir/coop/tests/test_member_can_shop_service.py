import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import ShiftUserData
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMemberCanShopService(TapirFactoryTestBase):
    REFERENCE_TIME = timezone.make_aware(datetime.datetime(year=2024, month=6, day=1))

    def test_canShop_memberCanShop_annotatedWithTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create(
            share_owner__nb_shares=1, share_owner__is_investing=False
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

        self.assertTrue(
            MemberCanShopService.can_shop(tapir_user.share_owner, self.REFERENCE_TIME)
        )

    def test_canShop_memberHasNoTapirUser_annotatedWithFalse(
        self,
    ):
        share_owner = ShareOwnerFactory.create(nb_shares=1)
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

        self.assertFalse(
            MemberCanShopService.can_shop(share_owner, self.REFERENCE_TIME)
        )

    def test_canShop_memberIsNotActive_annotatedWithFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create(
            share_owner__nb_shares=1, share_owner__is_investing=False
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=1)
        )

        self.assertFalse(
            MemberCanShopService.can_shop(tapir_user.share_owner, self.REFERENCE_TIME)
        )

    def test_canShop_memberIsFrozen_annotatedWithFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create(
            share_owner__nb_shares=1, share_owner__is_investing=False
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        self.assertFalse(
            MemberCanShopService.can_shop(tapir_user.share_owner, self.REFERENCE_TIME)
        )

    def test_annotateShareOwnerQuerysetWithShoppingStatusAtDatetime_memberCanShop_annotatedWithTrue(
        self,
    ):
        TapirUserFactory.create(
            share_owner__nb_shares=1, share_owner__is_investing=False
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

        queryset = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), self.REFERENCE_TIME
        )

        self.assertEqual(1, queryset.count())
        self.assertTrue(
            getattr(queryset.first(), MemberCanShopService.ANNOTATION_CAN_SHOP)
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.first(), MemberCanShopService.ANNOTATION_CAN_SHOP_DATE_CHECK
            ),
        )

    def test_annotateShareOwnerQuerysetWithShoppingStatusAtDatetime_memberHasNoTapirUser_annotatedWithFalse(
        self,
    ):
        ShareOwnerFactory.create(nb_shares=1)
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )

        queryset = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), self.REFERENCE_TIME
        )

        self.assertFalse(
            getattr(queryset.first(), MemberCanShopService.ANNOTATION_CAN_SHOP)
        )

    def test_annotateShareOwnerQuerysetWithShoppingStatusAtDatetime_memberIsNotActive_annotatedWithFalse(
        self,
    ):
        TapirUserFactory.create(
            share_owner__nb_shares=1, share_owner__is_investing=False
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=1)
        )

        queryset = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), self.REFERENCE_TIME
        )

        self.assertFalse(
            getattr(queryset.first(), MemberCanShopService.ANNOTATION_CAN_SHOP)
        )

    def test_annotateShareOwnerQuerysetWithShoppingStatusAtDatetime_memberIsFrozen_annotatedWithFalse(
        self,
    ):
        TapirUserFactory.create(
            share_owner__nb_shares=1, share_owner__is_investing=False
        )
        ShareOwnership.objects.update(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftUserData.objects.update(is_frozen=True)

        queryset = MemberCanShopService.annotate_share_owner_queryset_with_shopping_status_at_datetime(
            ShareOwner.objects.all(), self.REFERENCE_TIME
        )

        self.assertFalse(
            getattr(queryset.first(), MemberCanShopService.ANNOTATION_CAN_SHOP)
        )

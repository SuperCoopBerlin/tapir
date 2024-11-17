import datetime

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)

from tapir.coop.models import MembershipResignation, ShareOwnership, MembershipPause
from tapir.shifts.models import ShiftSlot, ShiftAttendance, ShiftAttendanceTemplate
from tapir.coop.tests.factories import (
    MembershipResignationFactory,
    ShareOwnerFactory,
    MembershipPauseFactory,
)
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.services.MembershipResignationService import (
    MembershipResignationService,
)


class TestMembershipResignationService(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_updateShiftsAndSharesAndPayOutDay_SharesAndPayOutDayForResignationTypeBuyBack_transferredAndSet(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
        )
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation,
        )
        shares_after_update = resignation.share_owner.share_ownerships
        for share in shares_after_update.all():
            self.assertEqual(
                resignation.cancellation_date.replace(
                    day=31, month=12, year=resignation.cancellation_date.year + 3
                ),
                share.end_date,
            )

    def test_updateShiftsAndSharesAndPayOutDay_SharesAndPayOutDayForResignationTypeGiftToCoop_transferredAndSet(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.GIFT_TO_COOP,
        )
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation,
        )
        shares_after_update = resignation.share_owner.share_ownerships
        for share in shares_after_update.all():
            self.assertEqual(share.end_date, resignation.cancellation_date)

    def test_updateShiftsAndSharesAndPayOutDay_SharesAndPayOutDayForResignationTypeTransfer_transferredAndSet(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
        )
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation,
        )
        shares_after_update = resignation.share_owner.share_ownerships
        self.assertEqual(
            ShareOwnership.objects.filter(
                share_owner=resignation.transferring_shares_to,
                start_date=resignation.cancellation_date,
            ).count(),
            shares_after_update.count(),
        )
        for share in shares_after_update.all():
            self.assertEqual(share.end_date, None)

    def test_updateShifts_shiftsAndShiftAttendance_cancelled(self):
        tapir_user = TapirUserFactory.create()
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        shift_template = ShiftTemplateFactory.create()
        shift = ShiftFactory.create(start_time=self.NOW.replace(day=16))
        ShiftAttendance.objects.create(user=tapir_user, slot=shift.slots.first())
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=shift_template.slot_templates.first()
        )
        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation
        )
        self.assertEqual(ShiftAttendanceTemplate.objects.count(), 0)
        self.assertEqual(
            ShiftAttendance.objects.get(user=tapir_user).state,
            ShiftAttendance.State.CANCELLED,
        )

    def test_updateShifts_shiftsBeforeResignation_notCancelled(self):
        tapir_user = TapirUserFactory.create()
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner, cancellation_date=self.TODAY
        )
        shift_template = ShiftTemplateFactory.create()
        shift = ShiftFactory.create(start_time=self.NOW.replace(day=14))
        ShiftAttendance.objects.create(user=tapir_user, slot=shift.slots.first())
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user,
            slot_template=shift_template.slot_templates.first(),
        )
        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation
        )
        self.assertEqual(
            ShiftAttendance.objects.get(user=tapir_user).state,
            ShiftAttendance.State.PENDING,
        )
        self.assertEqual(ShiftAttendanceTemplate.objects.count(), 0)

    def test_deleteEndDates_endDatesOfShares_removedFromShares(self):
        share_owner = ShareOwnerFactory.create(
            nb_shares=1,
        )
        ShareOwnership.objects.filter(share_owner=share_owner).update(
            end_date=datetime.datetime(year=2024, month=3, day=21),
        )
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        MembershipResignationService.delete_end_dates(resignation=resignation)
        shares = ShareOwnership.objects.filter(share_owner=resignation.share_owner)
        for share in shares:
            self.assertEqual(share.end_date, None)

    def test_deleteShareownerMembershippauses_pauseThatsEndsAfterPayOutDay_updatedToNewDate(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=1995, month=6, day=20),
        )
        pause_that_ends_after_pay_out_day = MembershipPauseFactory.create(
            share_owner=resignation.share_owner,
            start_date=datetime.date(year=1990, month=1, day=12),
            end_date=datetime.date(year=2000, month=6, day=20),
        )
        MembershipResignationService.delete_shareowner_membershippauses(
            resignation=resignation
        )
        pause_that_ends_after_pay_out_day.refresh_from_db()
        self.assertEqual(
            pause_that_ends_after_pay_out_day.end_date, resignation.pay_out_day
        )

    def test_deleteShareownerMembershippauses_pauseWithNoEndDate_getsDeleted(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=1995, month=6, day=20),
        )
        pause_with_no_end_date = MembershipPauseFactory.create(
            share_owner=resignation.share_owner,
            start_date=datetime.date(year=2001, month=6, day=20),
            end_date=None,
        )
        MembershipResignationService.delete_shareowner_membershippauses(
            resignation=resignation
        )
        self.assertFalse(
            MembershipPause.objects.filter(id=pause_with_no_end_date.id).exists()
        )

    def test_deleteShareownerMembershippauses_pauseWithNoEndDateAndStartDateAndSmallerThanPayOutDay_endDateSetToCancellationDate(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=1995, month=6, day=20),
        )
        pause_with_smaller_start_date = MembershipPauseFactory.create(
            share_owner=resignation.share_owner,
            start_date=datetime.date(year=1990, month=1, day=12),
            end_date=None,
        )
        MembershipResignationService.delete_shareowner_membershippauses(
            resignation=resignation
        )
        pause_with_smaller_start_date.refresh_from_db()
        self.assertEqual(
            pause_with_smaller_start_date.end_date, resignation.cancellation_date
        )

    def test_updateShiftsAndSharesAndPayOutDay_resignationTransferringShares_toSameMember(
        self,
    ):
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation_one = MembershipResignationFactory.create(
            share_owner=ShareOwnerFactory.create(nb_shares=1),
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
            transferring_shares_to=share_owner,
        )
        resignation_two = MembershipResignationFactory.create(
            share_owner=ShareOwnerFactory.create(nb_shares=1),
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
            transferring_shares_to=share_owner,
        )
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation_one
        )
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation_two
        )
        share_owner.refresh_from_db()
        self.assertTrue(share_owner.num_shares() == 4)

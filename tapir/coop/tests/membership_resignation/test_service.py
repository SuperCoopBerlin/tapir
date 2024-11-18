import datetime

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.models import (
    MembershipResignation,
    MembershipPause,
    ShareOwner,
)
from tapir.coop.services.MembershipResignationService import (
    MembershipResignationService,
)
from tapir.coop.tests.factories import (
    MembershipResignationFactory,
    ShareOwnerFactory,
    MembershipPauseFactory,
)
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
)
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestMembershipResignationService(FeatureFlagTestMixin, TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=9, day=15)
    TODAY = NOW.date()

    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(feature_flag_membership_resignation, True)
        mock_timezone_now(self, self.NOW)

    def test_updateShiftsAndSharesAndPayOutDay_resignationTypeBuyBack_sharesEndDateAndPayOutDaySetToThreeYearsAfterResignation(
        self,
    ):
        self.login_as_member_office_user()
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=self.TODAY,
        )

        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation,
        )

        resignation.refresh_from_db()
        expected_pay_out_day = datetime.date(year=2027, month=12, day=31)
        self.assertEqual(expected_pay_out_day, resignation.pay_out_day)
        for share in share_owner.share_ownerships.all():
            self.assertEqual(
                datetime.date(year=2027, month=12, day=31),
                share.end_date,
            )

    def test_updateShiftsAndSharesAndPayOutDay_resignationTypeGiftToCoop_sharesEndDateAndPayOutDaySetToResignationDate(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.GIFT_TO_COOP,
            cancellation_date=self.TODAY,
        )

        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation,
        )

        resignation.refresh_from_db()
        self.assertEqual(self.TODAY, resignation.pay_out_day)
        for share in share_owner.share_ownerships.all():
            self.assertEqual(share.end_date, self.TODAY)

    def test_updateShiftsAndSharesAndPayOutDay_resignationTypeTransfer_newSharesCreatedForReceivingMember(
        self,
    ):
        self.login_as_member_office_user()
        gifting_member = ShareOwnerFactory.create(nb_shares=2)
        receiving_member = ShareOwnerFactory.create(nb_shares=1)
        share_of_receiving_member_before_transfer = (
            receiving_member.share_ownerships.first()
        )
        resignation = MembershipResignationFactory.create(
            share_owner=gifting_member,
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
            cancellation_date=self.TODAY,
            transferring_shares_to=receiving_member,
        )

        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation,
        )

        shares_of_receiving_member = (
            resignation.transferring_shares_to.share_ownerships.all()
        )
        self.assertEqual(3, resignation.transferring_shares_to.share_ownerships.count())
        for share in shares_of_receiving_member.all():
            if share == share_of_receiving_member_before_transfer:
                continue
            self.assertEqual(None, share.end_date)
            self.assertEqual(self.TODAY, share.start_date)

        shares_of_gifting_member = gifting_member.share_ownerships.all()
        self.assertEqual(2, shares_of_gifting_member.count())
        for share in shares_of_gifting_member.all():
            self.assertEqual(self.TODAY, share.end_date)

    def test_updateShifts_resigningMemberHasAttendanceInTheFuture_attendanceCancelled(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=tapir_user.share_owner
        )
        shift = ShiftFactory.create(start_time=self.NOW + datetime.timedelta(days=1))
        ShiftAttendance.objects.create(user=tapir_user, slot=shift.slots.first())

        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation
        )

        self.assertEqual(ShiftAttendanceTemplate.objects.count(), 0)
        self.assertEqual(
            ShiftAttendance.objects.get(user=tapir_user).state,
            ShiftAttendance.State.CANCELLED,
        )

    def test_updateShifts_resigningMemberHasAttendanceTemplate_attendanceTemplateDeleted(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        resignation = MembershipResignationFactory.build(
            share_owner=tapir_user.share_owner
        )
        shift_template = ShiftTemplateFactory.create()
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=shift_template.slot_templates.first()
        )

        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation
        )

        self.assertEqual(ShiftAttendanceTemplate.objects.count(), 0)

    def test_updateShifts_resigningMemberHasAttendancesBeforeResignationDate_attendancesNotUpdated(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=tapir_user.share_owner, cancellation_date=self.TODAY
        )
        shift = ShiftFactory.create(start_time=self.NOW - datetime.timedelta(days=1))
        ShiftAttendance.objects.create(
            user=tapir_user,
            slot=shift.slots.first(),
            state=ShiftAttendance.State.PENDING,
        )

        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation
        )

        self.assertEqual(
            ShiftAttendance.objects.get(user=tapir_user).state,
            ShiftAttendance.State.PENDING,
        )

    def test_deleteEndDates_default_sharesEndDateRemoved(self):
        share_owner = ShareOwnerFactory.create(
            nb_shares=2,
        )
        share_owner.share_ownerships.update(
            end_date=datetime.datetime(year=2024, month=3, day=21),
        )
        resignation = MembershipResignationFactory.build(share_owner=share_owner)

        MembershipResignationService.delete_end_dates(resignation=resignation)

        for share in share_owner.share_ownerships.all():
            self.assertEqual(None, share.end_date)

    def test_updateMembershipPauses_pauseEndsAfterPayOutDay_pauseEndDateSetToPayOutDay(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=1995, month=6, day=20),
        )
        pause = MembershipPauseFactory.create(
            share_owner=resignation.share_owner,
            start_date=datetime.date(year=1990, month=1, day=12),
            end_date=datetime.date(year=2000, month=6, day=20),
        )

        MembershipResignationService.update_membership_pauses(resignation=resignation)

        pause.refresh_from_db()
        self.assertEqual(
            pause.end_date,
            datetime.date(year=1998, month=12, day=31),
        )

    def test_updateMembershipPauses_pauseStartsAfterPayOutDay_pauseDeleted(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=1995, month=6, day=20),
        )
        MembershipPauseFactory.create(
            share_owner=resignation.share_owner,
            start_date=datetime.date(year=2001, month=6, day=20),
            end_date=None,
        )

        MembershipResignationService.update_membership_pauses(resignation=resignation)

        self.assertFalse(MembershipPause.objects.exists())

    def test_updateMembershipPauses_pauseHasNoEnd_pauseEndDateSetToPayOutDay(
        self,
    ):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=datetime.date(year=1995, month=6, day=20),
        )
        pause = MembershipPauseFactory.create(
            share_owner=resignation.share_owner,
            start_date=datetime.date(year=1995, month=1, day=12),
            end_date=None,
        )
        MembershipResignationService.update_membership_pauses(resignation=resignation)
        pause.refresh_from_db()
        self.assertEqual(pause.end_date, datetime.date(year=1998, month=12, day=31))

    def test_updateShiftsAndSharesAndPayOutDay_twoResignationTransferingToSameMember_receivingMemberReceivesAllShares(
        self,
    ):
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation_one = MembershipResignationFactory.build(
            share_owner=ShareOwnerFactory.create(nb_shares=1),
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
            transferring_shares_to=share_owner,
        )
        resignation_two = MembershipResignationFactory.build(
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

        self.assertEqual(4, share_owner.share_ownerships.count())

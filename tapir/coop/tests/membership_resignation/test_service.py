import datetime
from unittest.mock import patch, Mock

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
    DeleteShiftAttendanceTemplateLogEntry,
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
        actor = self.login_as_member_office_user()
        share_owner: ShareOwner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.BUY_BACK,
            cancellation_date=self.TODAY,
        )

        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation, actor=actor
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
        actor = self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=2)
        resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=MembershipResignation.ResignationType.GIFT_TO_COOP,
            cancellation_date=self.TODAY,
        )

        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation, actor=actor
        )

        resignation.refresh_from_db()
        self.assertEqual(self.TODAY, resignation.pay_out_day)
        for share in share_owner.share_ownerships.all():
            self.assertEqual(share.end_date, self.TODAY)

    def test_updateShiftsAndSharesAndPayOutDay_resignationTypeTransfer_newSharesCreatedForReceivingMember(
        self,
    ):
        actor = self.login_as_member_office_user()
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
            resignation=resignation, actor=actor
        )

        shares_of_receiving_member = (
            resignation.transferring_shares_to.share_ownerships.all()
        )
        self.assertEqual(3, resignation.transferring_shares_to.share_ownerships.count())
        shares_of_gifting_member = list(gifting_member.share_ownerships.all())
        for share in shares_of_receiving_member.all():
            if share == share_of_receiving_member_before_transfer:
                self.assertIsNone(share.transferred_from)
                continue
            self.assertEqual(None, share.end_date)
            self.assertEqual(self.TODAY, share.start_date)
            self.assertIn(share.transferred_from, gifting_member.share_ownerships.all())
            shares_of_gifting_member.remove(
                share.transferred_from
            )  # making sure that there are no two shares with the same "transferred_from"

        shares_of_gifting_member = gifting_member.share_ownerships.all()
        self.assertEqual(2, shares_of_gifting_member.count())
        for share in shares_of_gifting_member.all():
            self.assertEqual(self.TODAY, share.end_date)
            self.assertIsNone(share.transferred_from)

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
            tapir_user=tapir_user,
            resignation=resignation,
            actor=TapirUserFactory.create(),
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
            tapir_user=tapir_user,
            resignation=resignation,
            actor=TapirUserFactory.create(),
        )

        self.assertEqual(ShiftAttendanceTemplate.objects.count(), 0)
        self.assertEqual(DeleteShiftAttendanceTemplateLogEntry.objects.count(), 1)

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
            tapir_user=tapir_user,
            resignation=resignation,
            actor=TapirUserFactory.create(),
        )

        self.assertEqual(
            ShiftAttendance.objects.get(user=tapir_user).state,
            ShiftAttendance.State.PENDING,
        )

    @patch.object(MembershipResignationService, "delete_end_dates")
    @patch.object(MembershipResignationService, "delete_transferred_share_ownerships")
    def test_onResignationDeleted_default_classAllRelevantFunctions(
        self,
        mock_delete_transferred_share_ownerships: Mock,
        mock_delete_end_dates: Mock,
    ):
        resignation = MembershipResignationFactory.create()

        MembershipResignationService.on_resignation_deleted(resignation)

        mock_delete_transferred_share_ownerships.assert_called_once_with(resignation)
        mock_delete_end_dates.assert_called_once_with(resignation)

    def test_deleteEndDates_default_sharesEndDateSetToNone(self):
        cancellation_date = datetime.datetime(year=2024, month=3, day=21)
        share_owner = ShareOwnerFactory.create(
            nb_shares=2,
        )
        share_owner.share_ownerships.update(
            end_date=cancellation_date,
        )
        resignation = MembershipResignationFactory.build(
            share_owner=share_owner, cancellation_date=cancellation_date
        )

        MembershipResignationService.delete_end_dates(resignation=resignation)

        for share in share_owner.share_ownerships.all():
            self.assertEqual(None, share.end_date)

    def test_deleteEndDates_someSharesEndedBeforeCancellation_thoseSharesKeepTheirEndDate(
        self,
    ):
        cancellation_date = datetime.datetime(year=2024, month=3, day=21)
        share_owner = ShareOwnerFactory.create(
            nb_shares=3,
        )
        share_owner.share_ownerships.update(
            end_date=cancellation_date,
        )
        resignation = MembershipResignationFactory.build(
            share_owner=share_owner, cancellation_date=cancellation_date
        )
        share_that_ended_before_cancellation = share_owner.share_ownerships.first()
        share_that_ended_before_cancellation.end_date = datetime.date(
            year=2024, month=1, day=15
        )
        share_that_ended_before_cancellation.save()

        MembershipResignationService.delete_end_dates(resignation=resignation)

        for share in share_owner.share_ownerships.all():
            if share == share_that_ended_before_cancellation:
                self.assertEqual(
                    datetime.date(year=2024, month=1, day=15), share.end_date
                )
            else:
                self.assertEqual(None, share.end_date)

    def test_deleteTransferredShareOwnerships_default_deletesAllOwnershipsOfChain(self):
        cancellation_date = datetime.datetime(year=2024, month=3, day=21)
        resigned_member = ShareOwnerFactory.create(
            nb_shares=3,
        )
        resigned_member.share_ownerships.update(
            end_date=cancellation_date,
        )

        # build a transfer chain
        first_recipient: ShareOwner = ShareOwnerFactory.create(nb_shares=2)
        # set start date for only one share in order to test that the second share doesn't get affected
        transferred_share = first_recipient.share_ownerships.first()
        transferred_share.transferred_from = resigned_member.share_ownerships.first()
        transferred_share.start_date = cancellation_date
        transferred_share.save()

        second_recipient: ShareOwner = ShareOwnerFactory.create(nb_shares=1)
        second_recipient.share_ownerships.update(
            transferred_from=first_recipient.share_ownerships.first()
        )

        resignation = MembershipResignationFactory.build(
            share_owner=resigned_member,
            cancellation_date=cancellation_date,
            resignation_type=MembershipResignation.ResignationType.TRANSFER,
            transferring_shares_to=first_recipient,
        )

        MembershipResignationService.delete_transferred_share_ownerships(
            resignation=resignation
        )

        self.assertEqual(3, resigned_member.share_ownerships.count())
        self.assertEqual(1, first_recipient.share_ownerships.count())
        self.assertEqual(0, second_recipient.share_ownerships.count())

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

    def test_updateShiftsAndSharesAndPayOutDay_twoResignationTransferringToSameMember_receivingMemberReceivesAllShares(
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
            resignation=resignation_one, actor=TapirUserFactory.create()
        )
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=resignation_two, actor=TapirUserFactory.create()
        )

        self.assertEqual(4, share_owner.share_ownerships.count())

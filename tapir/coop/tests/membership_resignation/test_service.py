import datetime
from icecream import ic

from django.urls import reverse
from http import HTTPStatus

from tapir.coop.config import feature_flag_membership_resignation
from tapir.utils.tests_utils import (
    FeatureFlagTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)

from tapir.coop.models import MembershipResignation, ShareOwnership
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

    def test_update_shifts_and_shares(self):
        resignations = [
            MembershipResignation.ResignationType.BUY_BACK,
            MembershipResignation.ResignationType.GIFT_TO_COOP,
            MembershipResignation.ResignationType.TRANSFER,
        ]

        self.login_as_member_office_user()
        for resignation in resignations:
            share_owner = ShareOwnerFactory.create(nb_shares=2)
            resignation = MembershipResignationFactory.create(
            share_owner=share_owner,
            resignation_type=resignation,
        )
            MembershipResignationService.update_shifts_and_shares(
                        resignation=resignation,
                    )
            shares_after_update = resignation.share_owner.share_ownerships
            match resignation:
                case MembershipResignation.ResignationType.BUY_BACK:
                    for share in shares_after_update.all():
                        self.assertEqual(
                            resignation.cancellation_date.replace(
                                day=31, month=12, year=resignation.cancellation_date.year + 3
                            ),
                            share.end_date,
                        )
                case MembershipResignation.ResignationType.GIFT_TO_COOP:
                    for share in shares_after_update.all():
                        self.assertEqual(share.end_date, resignation.cancellation_date)
                case MembershipResignation.ResignationType.TRANSFER:
                    self.assertEqual(ShareOwnership.objects.get(
                        share_owner=resignation.transferring_shares_to,
                        start_date=resignation.cancellation_date).count(),
                        shares_after_update.count()
                        )
                    self.assertEqual(share.end_date, resignation.cancellation_date)

    def test_update_shifts(self):
        tapir_user = TapirUserFactory.create()
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        shift_template = ShiftTemplateFactory.create()
        shift = ShiftFactory.create()
        ShiftAttendance.objects.create(
            user=tapir_user, slot=ShiftSlot.objects.filter(shift=shift).first()
        )   
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=shift_template.slot_templates.first()
        )
        MembershipResignationService.update_shifts(
            tapir_user=tapir_user, resignation=resignation
        )
        self.assertEqual(ShiftAttendanceTemplate.objects.count(), 0)
        self.assertEqual(ShiftAttendance.objects.get(user=tapir_user).state, ShiftAttendance.State.CANCELLED)
        
    def test_delete_end_dates(self):
        share_owner = ShareOwnerFactory.create(nb_shares=1)
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        MembershipResignationService.delete_end_dates(member=resignation)
        shares = ShareOwnership.objects.filter(share_owner=resignation.share_owner)
        for share in shares:
            self.assertEqual(share.end_date, None)
            
    def test_delete_shareowner_membershippauses(self):
        share_owner = ShareOwnerFactory.create()
        resignation = MembershipResignationFactory.create(share_owner=share_owner)
        pause = MembershipPauseFactory.create(share_owner=resignation.share_owner)
        MembershipResignationService.delete_shareowner_membershippauses(resignation=resignation)
        if pause.end_date is not None:
            if resignation.pay_out_day is not None:
                if resignation.pay_out_day <= pause.end_date:
                    self.assertEqual(pause.end_date, resignation.pay_out_day)
                elif pause.start_date > resignation.pay_out_day:
                    self.assertEqual(pause.count(), 0)
            else:
                if resignation.cancellation_date <= pause.end_date:
                    self.assertEqual(pause.end_date, resignation.cancellation_date)
                elif pause.start_date > resignation.cancellation_date:
                    self.assertEqual(pause.count(), 0)
        else:
            self.assertEqual(pause.end_date, resignation.cancellation_date)

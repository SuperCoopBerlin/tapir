import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftTemplate,
)
from tapir.shifts.tests.factories import ShiftFactory, ShiftTemplateFactory
from tapir.shifts.tests.utils import (
    register_user_to_shift,
    register_user_to_shift_template,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMemberSelfRegisters(TapirFactoryTestBase):
    VIEW_NAME_CANCEL_SHIFT = "shifts:cancel_shift"
    A_CANCELLATION_REASON = "A cancellation reason"

    def test_flying_member_gets_attendance_cancelled(self):
        user = TapirUserFactory.create(is_in_member_office=False)
        self.login_as_member_office_user()
        shift = ShiftFactory.create()
        register_user_to_shift(self.client, user, shift)

        response = self.client.post(
            reverse(self.VIEW_NAME_CANCEL_SHIFT, args=[shift.id]),
            {"cancelled_reason": self.A_CANCELLATION_REASON},
        )

        self.assertRedirects(
            response,
            shift.get_absolute_url(),
            msg_prefix="The request should redirect to the shift's page.",
        )

        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift).state,
            ShiftAttendance.State.CANCELLED,
            "The attendance is not from an ABCD shift, it should get cancelled.",
        )
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            0,
            "Because the attendance got cancelled, the account balance should have stayed at 0.",
        )

    def test_abcd_member_gets_attendance_excused(self):
        user = TapirUserFactory.create(is_in_member_office=False)
        self.login_as_member_office_user()
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift = shift_template.create_shift(
            timezone.now().date() + datetime.timedelta(days=2)
        )
        register_user_to_shift_template(self.client, user, shift_template)

        response = self.client.post(
            reverse(self.VIEW_NAME_CANCEL_SHIFT, args=[shift.id]),
            {"cancelled_reason": self.A_CANCELLATION_REASON},
        )

        self.assertRedirects(
            response,
            shift.get_absolute_url(),
            msg_prefix="The request should redirect to the shift's page.",
        )

        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift).state,
            ShiftAttendance.State.MISSED_EXCUSED,
            "The attendance is from an ABCD shift, it should get excused.",
        )
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            1,
            "Because the attendance got excused, the account balance should have increased to 1.",
        )

    def test_member_registering_after_cancellation(self):
        user = TapirUserFactory.create(is_in_member_office=False)
        self.login_as_member_office_user()
        shift_template: ShiftTemplate = ShiftTemplateFactory.create()
        shift = shift_template.create_shift(
            timezone.now().date() + datetime.timedelta(days=2)
        )
        self.client.post(
            reverse(self.VIEW_NAME_CANCEL_SHIFT, args=[shift.id]),
            {"cancelled_reason": self.A_CANCELLATION_REASON},
        )

        register_user_to_shift_template(self.client, user, shift_template)

        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift).state,
            ShiftAttendance.State.MISSED_EXCUSED,
            "If a user gets registered to an ABCD shift that has cancelled instances, "
            "they should get excused upon registration to the ABCD shift.",
        )
        self.assertEqual(
            user.shift_user_data.get_account_balance(),
            1,
            "Because the attendance got excused, the account balance should have increased to 1.",
        )

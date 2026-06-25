import datetime

from django.core import mail

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner, ShareOwnership
from tapir.shifts.models import ShiftAccountEntry
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.shifts.tests.utils import (
    register_user_to_shift_template,
)
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestRegisterUserToShiftTemplateSlotView(TapirFactoryTestBase):
    def setUp(self) -> None:
        mock_timezone_now(test=self, now=datetime.datetime(year=1997, month=9, day=13))

        self.login_as_member_office_user()
        self.user = TapirUserFactory.create()
        ShareOwnership.objects.update(
            start_date=datetime.date(year=1997, month=1, day=1)
        )
        ShareOwner.objects.update(is_investing=False)
        self.shift_template = ShiftTemplateFactory.create()
        ShiftAccountEntry.objects.create(
            user=self.user,
            value=-4,
            date=datetime.datetime(year=1995, month=1, day=1, tzinfo=datetime.UTC),
        )

    def test_post_memberRegistersToShiftTemplateInTheNearFutureAndIsFrozen_memberIsUnfrozen(
        self,
    ):
        shift_user_data = self.user.shift_user_data
        shift_user_data.is_frozen = True
        shift_user_data.save()

        self.shift_template.create_shift_if_necessary(
            start_date=datetime.datetime(
                year=1997, month=9, day=15, tzinfo=datetime.UTC
            )
        )

        register_user_to_shift_template(
            client=self.client, shift_template=self.shift_template, user=self.user
        )

        shift_user_data.refresh_from_db()
        self.assertFalse(shift_user_data.is_frozen)

    def test_post_memberRegistersToShiftTemplateInTheFarFutureAndIsFrozen_doNothing(
        self,
    ):
        shift_user_data = self.user.shift_user_data
        shift_user_data.is_frozen = True
        shift_user_data.save()

        self.shift_template.create_shift_if_necessary(
            start_date=datetime.datetime(
                year=1997, month=12, day=31, tzinfo=datetime.UTC
            )
        )

        register_user_to_shift_template(
            client=self.client, shift_template=self.shift_template, user=self.user
        )

        shift_user_data.refresh_from_db()
        self.assertTrue(shift_user_data.is_frozen)

    def test_post_memberRegistersToShiftTemplateInTheNearFutureAndIsNotFrozen_doNothing(
        self,
    ):
        shift_user_data = self.user.shift_user_data
        shift_user_data.is_frozen = False
        shift_user_data.save()

        self.shift_template.create_shift_if_necessary(
            start_date=datetime.datetime(
                year=1997, month=9, day=15, tzinfo=datetime.UTC
            )
        )

        register_user_to_shift_template(
            client=self.client, shift_template=self.shift_template, user=self.user
        )

        shift_user_data.refresh_from_db()
        self.assertFalse(shift_user_data.is_frozen)
        self.assertEqual(0, len(mail.outbox))

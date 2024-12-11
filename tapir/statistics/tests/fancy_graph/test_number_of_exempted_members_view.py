import datetime

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwnership, ShareOwner
from tapir.shifts.models import ShiftExemption, ShiftUserData
from tapir.statistics.views.fancy_graph.number_of_exempted_members_view import (
    NumberOfExemptedMembersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestNumberOfExemptedMembersAtDateView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2022, month=7, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2023, month=8, day=15, hour=18)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    @classmethod
    def create_member_where_the_only_reason_for_not_working_is_an_exemption(cls):
        tapir_user = TapirUserFactory.create(
            date_joined=cls.REFERENCE_TIME - datetime.timedelta(days=1),
            share_owner__is_investing=False,
        )
        ShareOwnership.objects.update(
            start_date=cls.REFERENCE_TIME.date() - datetime.timedelta(days=1)
        )
        ShiftExemption.objects.create(
            start_date=cls.REFERENCE_TIME.date() - datetime.timedelta(days=1),
            end_date=cls.REFERENCE_TIME.date() + datetime.timedelta(days=1),
            shift_user_data=tapir_user.shift_user_data,
        )

    def test_calculateDatapoint_exemptedMemberThatWouldWorkOtherwise_counted(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()

        result = NumberOfExemptedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)

    def test_calculateDatapoint_memberHasExemptionButIsNotActive_notCounted(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        ShareOwner.objects.update(is_investing=True)

        result = NumberOfExemptedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberHasExemptionButIsFrozen_notCounted(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        ShiftUserData.objects.update(is_frozen=True)

        result = NumberOfExemptedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberHasExemptionButJoinedAfterDate_notCounted(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        TapirUser.objects.update(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )

        result = NumberOfExemptedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberHasExemptionThatIsNotActiveAtGivenDate_notCounted(
        self,
    ):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        ShiftExemption.objects.update(
            start_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=1),
            end_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=2),
        )

        result = NumberOfExemptedMembersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

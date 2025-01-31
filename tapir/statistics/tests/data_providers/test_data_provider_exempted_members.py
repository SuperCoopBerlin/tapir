import datetime

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftExemption, ShiftUserData
from tapir.statistics.services.data_providers.data_provider_exempted_members import (
    DataProviderExemptedMembers,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_is_working,
)


class TestDataProviderExemptedMembersAtDate(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2022, month=7, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2023, month=8, day=15, hour=18)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def create_member_where_the_only_reason_for_not_working_is_an_exemption(self):
        tapir_user = create_member_that_is_working(self, self.REFERENCE_TIME)
        ShiftExemption.objects.create(
            start_date=self.REFERENCE_TIME.date() - datetime.timedelta(days=1),
            end_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=1),
            shift_user_data=tapir_user.shift_user_data,
        )
        return tapir_user

    def test_getQueryset_exemptedMemberThatWouldWorkOtherwise_included(self):
        tapir_user = (
            self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        )

        queryset = DataProviderExemptedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(1, queryset.count())
        self.assertIn(tapir_user.share_owner, queryset)

    def test_getQueryset_memberHasExemptionButIsNotActive_notIncluded(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        ShareOwner.objects.update(is_investing=True)

        queryset = DataProviderExemptedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberHasExemptionButIsFrozen_notIncluded(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        ShiftUserData.objects.update(is_frozen=True)

        queryset = DataProviderExemptedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberHasExemptionButJoinedAfterDate_notIncluded(self):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        TapirUser.objects.update(
            date_joined=self.REFERENCE_TIME + datetime.timedelta(days=1)
        )

        queryset = DataProviderExemptedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

    def test_getQueryset_memberHasExemptionThatIsNotActiveAtGivenDate_notIncluded(
        self,
    ):
        self.create_member_where_the_only_reason_for_not_working_is_an_exemption()
        ShiftExemption.objects.update(
            start_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=1),
            end_date=self.REFERENCE_TIME.date() + datetime.timedelta(days=2),
        )

        queryset = DataProviderExemptedMembers.get_queryset(self.REFERENCE_TIME)

        self.assertEqual(0, queryset.count())

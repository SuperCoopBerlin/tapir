import datetime

from django.utils import timezone

from tapir.statistics.views.fancy_graph.number_of_shift_partners_view import (
    NumberOfShiftPartnersAtDateView,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_is_working,
)


class TestNumberOfShiftPartnersView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=6, day=15, hour=12)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_calculateDatapoint_memberHasPartnerButIsNotWorking_notCounted(self):
        member_with_partner = create_member_that_is_working(self, self.REFERENCE_TIME)
        member_that_is_partner_of = create_member_that_is_working(
            self, self.REFERENCE_TIME
        )
        member_with_partner.shift_user_data.shift_partner = (
            member_that_is_partner_of.shift_user_data
        )
        member_with_partner.shift_user_data.save()

        member_with_partner.share_owner.is_investing = True
        member_with_partner.share_owner.save()

        result = NumberOfShiftPartnersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsWorkingButHasNoPartner_notCounted(self):
        create_member_that_is_working(self, self.REFERENCE_TIME)

        result = NumberOfShiftPartnersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(0, result)

    def test_calculateDatapoint_memberIsWorkingAndHasAPartner_counted(self):
        member_with_partner = create_member_that_is_working(self, self.REFERENCE_TIME)
        member_that_is_partner_of = create_member_that_is_working(
            self, self.REFERENCE_TIME
        )
        member_with_partner.shift_user_data.shift_partner = (
            member_that_is_partner_of.shift_user_data
        )
        member_with_partner.shift_user_data.save()

        result = NumberOfShiftPartnersAtDateView().calculate_datapoint(
            self.REFERENCE_TIME
        )

        self.assertEqual(1, result)
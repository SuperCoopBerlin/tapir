import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftUserData, ShiftExemption
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestAnnotateWithWorkingStatus(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2024, month=10, day=5)
    REFERENCE_DATETIME = timezone.make_aware(
        datetime.datetime(year=2024, month=6, day=10)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    def test_annotateShiftUserDataQuerysetWithWorkingStatusAtDatetime_memberShouldWork_annotatesTrue(
        self,
    ):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_DATETIME - datetime.timedelta(days=1)
        )

        result = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), self.REFERENCE_DATETIME
        )

        shift_user_data = result.get()
        self.assertEqual(
            True,
            getattr(
                shift_user_data, ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE
            ),
        )
        self.assertEqual(
            self.REFERENCE_DATETIME,
            getattr(
                shift_user_data,
                ShiftExpectationService.ANNOTATION_IS_WORKING_DATE_CHECK,
            ),
        )

    def test_annotateShiftUserDataQuerysetWithWorkingStatusAtDatetime_memberIsFrozen_annotatesFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_DATETIME - datetime.timedelta(days=1)
        )
        tapir_user.shift_user_data.is_frozen = True
        tapir_user.shift_user_data.save()

        result = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), self.REFERENCE_DATETIME
        )

        shift_user_data = result.get()
        self.assertEqual(
            False,
            getattr(
                shift_user_data, ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE
            ),
        )

    def test_annotateShiftUserDataQuerysetWithWorkingStatusAtDatetime_memberJoinedAfterData_annotatesFalse(
        self,
    ):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_DATETIME + datetime.timedelta(days=1)
        )

        result = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), self.REFERENCE_DATETIME
        )

        shift_user_data = result.get()
        self.assertEqual(
            False,
            getattr(
                shift_user_data, ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE
            ),
        )

    def test_annotateShiftUserDataQuerysetWithWorkingStatusAtDatetime_memberIsNotActive_annotatesFalse(
        self,
    ):
        TapirUserFactory.create(
            date_joined=self.REFERENCE_DATETIME + datetime.timedelta(days=1),
            share_owner__nb_shares=0,
        )

        result = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), self.REFERENCE_DATETIME
        )

        shift_user_data = result.get()
        self.assertEqual(
            False,
            getattr(
                shift_user_data, ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE
            ),
        )

    def test_annotateShiftUserDataQuerysetWithWorkingStatusAtDatetime_memberHasExemption_annotatesFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create(
            date_joined=self.REFERENCE_DATETIME + datetime.timedelta(days=1)
        )
        ShiftExemption.objects.create(
            start_date=self.REFERENCE_DATETIME.date() - datetime.timedelta(days=1),
            end_date=self.REFERENCE_DATETIME.date() + datetime.timedelta(days=1),
            shift_user_data=tapir_user.shift_user_data,
        )

        result = ShiftExpectationService.annotate_shift_user_data_queryset_with_working_status_at_datetime(
            ShiftUserData.objects.all(), self.REFERENCE_DATETIME
        )

        shift_user_data = result.get()
        self.assertEqual(
            False,
            getattr(
                shift_user_data, ShiftExpectationService.ANNOTATION_IS_WORKING_AT_DATE
            ),
        )

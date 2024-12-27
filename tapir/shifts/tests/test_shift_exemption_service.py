import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftUserData, ShiftExemption
from tapir.shifts.services.shift_exemption_service import ShiftExemptionService
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftExemptionService(TapirFactoryTestBase):
    def test_annotateShiftUserDataQuerysetWithHasExemptionAtDate_noExemptions_annotatesFalse(
        self,
    ):
        TapirUserFactory.create()

        queryset = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            ShiftUserData.objects.all(), timezone.now()
        )

        self.assertEqual(
            1,
            queryset.filter(
                **{ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE: False}
            ).count(),
        )

    def test_annotateShiftUserDataQuerysetWithHasExemptionAtDate_hasInvalidExemptions_annotatesFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()

        ShiftExemption.objects.create(  # in the past
            start_date=datetime.date(year=2023, month=1, day=1),
            end_date=datetime.date(year=2024, month=1, day=1),
            shift_user_data=tapir_user.shift_user_data,
        )

        ShiftExemption.objects.create(  # in the future
            start_date=datetime.date(year=2024, month=6, day=15),
            end_date=None,
            shift_user_data=tapir_user.shift_user_data,
        )

        queryset = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            ShiftUserData.objects.all(), datetime.date(year=2024, month=6, day=1)
        )

        self.assertEqual(
            1,
            queryset.filter(
                **{ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE: False}
            ).count(),
        )

    def test_annotateShiftUserDataQuerysetWithHasExemptionAtDate_hasValidInfiniteExemption_annotatesTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()

        ShiftExemption.objects.create(
            start_date=datetime.date(year=2023, month=1, day=1),
            end_date=None,
            shift_user_data=tapir_user.shift_user_data,
        )

        queryset = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            ShiftUserData.objects.all(), datetime.date(year=2024, month=6, day=1)
        )

        self.assertEqual(
            1,
            queryset.filter(
                **{ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE: True}
            ).count(),
        )

    def test_annotateShiftUserDataQuerysetWithHasExemptionAtDate_hasValidFiniteExemption_annotatesTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()

        ShiftExemption.objects.create(
            start_date=datetime.date(year=2024, month=6, day=1),
            end_date=datetime.date(year=2024, month=7, day=1),
            shift_user_data=tapir_user.shift_user_data,
        )

        queryset = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            ShiftUserData.objects.all(), datetime.date(year=2024, month=6, day=15)
        )

        self.assertEqual(
            1,
            queryset.filter(
                **{ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE: True}
            ).count(),
        )

import datetime
from unittest.mock import patch, Mock

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts import config
from tapir.shifts.models import (
    ShiftUserData,
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceMode,
)
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestFrozenStatusHistoryService(TapirFactoryTestBase):
    @staticmethod
    def create_annotated_shift_user_data(
        is_frozen: bool, annotation_time: datetime.datetime
    ):
        shift_user_data = ShiftUserData()
        setattr(
            shift_user_data,
            FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE,
            is_frozen,
        )
        setattr(
            shift_user_data,
            FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_DATE_CHECK,
            annotation_time,
        )
        return shift_user_data

    def test_isFrozenAtDatetime_annotationWithWrongDate_raisesError(self):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            True, reference_datetime
        )

        with self.assertRaises(ValueError):
            FrozenStatusHistoryService.is_frozen_at_datetime(
                shift_user_data,
                reference_datetime + datetime.timedelta(hours=1),
            )

    @patch.object(
        FrozenStatusHistoryService,
        "annotate_shift_user_data_queryset_with_is_frozen_at_datetime",
    )
    def test_isFrozenAtDatetime_alreadyAnnotated_dontAnnotateAgain(
        self, mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime: Mock
    ):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            True, reference_datetime
        )

        FrozenStatusHistoryService.is_frozen_at_datetime(
            shift_user_data,
            reference_datetime,
        )

        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime.assert_not_called()

    def test_isFrozenAtDatetime_annotatedFrozen_returnsTrue(self):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            True, reference_datetime
        )

        self.assertTrue(
            FrozenStatusHistoryService.is_frozen_at_datetime(
                shift_user_data,
                reference_datetime,
            )
        )

    def test_isFrozenAtDatetime_annotatedNotFrozen_returnsFalse(self):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            False, reference_datetime
        )

        self.assertFalse(
            FrozenStatusHistoryService.is_frozen_at_datetime(
                shift_user_data,
                reference_datetime,
            )
        )

    @patch.object(
        FrozenStatusHistoryService,
        "_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor",
    )
    @patch.object(
        FrozenStatusHistoryService,
        "_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor",
    )
    def test_annotateShiftUserDataQuerysetWithIsFrozenAtDatetime_givenDateIsBeforeRefactor_useCorrectAnnotationMethod(
        self,
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor: Mock,
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor: Mock,
    ):
        expected_result = Mock()
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor.return_value = (
            expected_result
        )
        reference_datetime = (
            config.ATTENDANCE_MODE_REFACTOR_DATETIME - datetime.timedelta(days=1)
        )

        actual_result = FrozenStatusHistoryService.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
            ShiftUserData.objects.none(),
            reference_datetime,
        )

        self.assertEqual(actual_result, expected_result)
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor.assert_called_once()
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor.assert_not_called()

    @patch.object(
        FrozenStatusHistoryService,
        "_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor",
    )
    @patch.object(
        FrozenStatusHistoryService,
        "_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor",
    )
    def test_annotateShiftUserDataQuerysetWithIsFrozenAtDatetime_givenDateIsAfterRefactor_useCorrectAnnotationMethod(
        self,
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor: Mock,
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor: Mock,
    ):
        expected_result = Mock()
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor.return_value = (
            expected_result
        )
        reference_datetime = (
            config.ATTENDANCE_MODE_REFACTOR_DATETIME + datetime.timedelta(days=1)
        )

        actual_result = FrozenStatusHistoryService.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
            ShiftUserData.objects.none(),
            reference_datetime,
        )

        self.assertEqual(actual_result, expected_result)
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor.assert_not_called()
        mock_annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor.assert_called_once()

    def test_annotateShiftUserDataQuerysetWithIsFrozenAtDatetimeBeforeRefactor_noRelevantLogEntry_annotatesCurrentValue(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = False
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()
        log_entry_in_the_past = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"attendance_mode": ShiftAttendanceMode.FROZEN},
            new_values={},
        )
        log_entry_in_the_past.created_date = reference_datetime - datetime.timedelta(
            days=1
        )
        log_entry_in_the_past.save()

        log_entry_irrelevant = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"shift_partner": "12"},
            new_values={"shift_partner": "13"},
        )
        log_entry_irrelevant.created_date = reference_datetime + datetime.timedelta(
            days=1
        )
        log_entry_irrelevant.save()

        queryset = FrozenStatusHistoryService._annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE,
            ),
            False,
        )

    def test_annotateShiftUserDataQuerysetWithIsFrozenAtDatetimeBeforeRefactor_hasRelevantLogEntry_annotatesLogEntryValue(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = False
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()
        relevant_log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"attendance_mode": ShiftAttendanceMode.FROZEN},
            new_values={},
        )
        relevant_log_entry.created_date = reference_datetime + datetime.timedelta(
            days=5
        )
        relevant_log_entry.save()

        not_relevant_log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"shift_partner": 182},
            new_values={"shift_partner": 25},
        )
        not_relevant_log_entry.created_date = reference_datetime + datetime.timedelta(
            days=3
        )
        not_relevant_log_entry.save()

        queryset = FrozenStatusHistoryService._annotate_shift_user_data_queryset_with_is_frozen_at_datetime_before_refactor(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE,
            ),
            True,
        )

    def test_annotateShiftUserDataQuerysetWithIsFrozenAtDatetimeAfterRefactor_noRelevantLogEntry_annotatesCurrentValue(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = False
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()
        log_entry_in_the_past = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": True},
            new_values={"is_frozen": False},
        )
        log_entry_in_the_past.created_date = reference_datetime - datetime.timedelta(
            days=1
        )
        log_entry_in_the_past.save()

        not_relevant_log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"shift_partner": 182},
            new_values={"shift_partner": 25},
        )
        not_relevant_log_entry.created_date = reference_datetime + datetime.timedelta(
            days=3
        )
        not_relevant_log_entry.save()

        queryset = FrozenStatusHistoryService._annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE,
            ),
            False,
        )

    def test_annotateShiftUserDataQuerysetWithIsFrozenAtDatetimeAfterRefactor_hasRelevantLogEntry_annotatesLogEntryValue(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = False
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()
        log_entry_in_the_past = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": True},
            new_values={"is_frozen": False},
        )
        log_entry_in_the_past.created_date = reference_datetime + datetime.timedelta(
            days=5
        )
        log_entry_in_the_past.save()

        not_relevant_log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"shift_partner": 182},
            new_values={"shift_partner": 25},
        )
        not_relevant_log_entry.created_date = reference_datetime + datetime.timedelta(
            days=3
        )
        not_relevant_log_entry.save()

        queryset = FrozenStatusHistoryService._annotate_shift_user_data_queryset_with_is_frozen_at_datetime_after_refactor(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE,
            ),
            True,
        )

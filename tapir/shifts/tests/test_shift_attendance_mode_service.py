import datetime
from unittest.mock import patch, Mock

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftUserData,
    ShiftAttendanceMode,
    CreateShiftAttendanceTemplateLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    create_attendance_template_log_entry_in_the_past,
)


class TestShiftAttendanceModeService(TapirFactoryTestBase):
    @staticmethod
    def create_annotated_shift_user_data(
        attendance_mode: str, annotation_time: datetime.datetime
    ):
        shift_user_data = ShiftUserData()
        setattr(
            shift_user_data,
            ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE,
            attendance_mode,
        )
        setattr(
            shift_user_data,
            ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_DATE_CHECK,
            annotation_time,
        )
        return shift_user_data

    def test_getAttendanceMode_annotationWithWrongDate_raisesError(self):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            ShiftAttendanceMode.FLYING, reference_datetime
        )

        with self.assertRaises(ValueError):
            ShiftAttendanceModeService.get_attendance_mode(
                shift_user_data,
                reference_datetime + datetime.timedelta(hours=1),
            )

    @patch.object(
        ShiftAttendanceModeService,
        "annotate_shift_user_data_queryset_with_attendance_mode_at_datetime",
    )
    def test_getAttendanceMode_alreadyAnnotated_dontAnnotateAgain(
        self, mock_annotate_shift_user_data_queryset_with_attendance_mode_at_date: Mock
    ):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            ShiftAttendanceMode.FLYING, reference_datetime
        )

        ShiftAttendanceModeService.get_attendance_mode(
            shift_user_data,
            reference_datetime,
        )

        mock_annotate_shift_user_data_queryset_with_attendance_mode_at_date.assert_not_called()

    def test_getAttendanceMode_annotatedFrozen_returnsFrozen(self):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            ShiftAttendanceMode.FROZEN, reference_datetime
        )

        self.assertEqual(
            ShiftAttendanceMode.FROZEN,
            ShiftAttendanceModeService.get_attendance_mode(
                shift_user_data,
                reference_datetime,
            ),
        )

    def test_getAttendanceMode_annotatedRegular_returnsRegular(self):
        reference_datetime = timezone.now()
        shift_user_data = self.create_annotated_shift_user_data(
            ShiftAttendanceMode.REGULAR, reference_datetime
        )

        self.assertEqual(
            ShiftAttendanceMode.REGULAR,
            ShiftAttendanceModeService.get_attendance_mode(
                shift_user_data,
                reference_datetime,
            ),
        )

    def test_annotateQuerysetWithHasAbcdAttendanceAtDate_noLogEntries_annotatesFalse(
        self,
    ):
        TapirUserFactory.create()
        reference_datetime = timezone.now()

        queryset = ShiftAttendanceModeService._annotate_queryset_with_has_abcd_attendance_at_datetime(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                ShiftAttendanceModeService.ANNOTATION_HAS_ABCD_ATTENDANCE_AT_DATE,
            ),
            False,
        )

    def test_annotateQuerysetWithHasAbcdAttendanceAtDate_moreDeleteThanCreateEntries_annotatesFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        reference_datetime = timezone.now()

        create_attendance_template_log_entry_in_the_past(
            CreateShiftAttendanceTemplateLogEntry, tapir_user, reference_datetime
        )
        create_attendance_template_log_entry_in_the_past(
            DeleteShiftAttendanceTemplateLogEntry, tapir_user, reference_datetime
        )

        queryset = ShiftAttendanceModeService._annotate_queryset_with_has_abcd_attendance_at_datetime(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                ShiftAttendanceModeService.ANNOTATION_HAS_ABCD_ATTENDANCE_AT_DATE,
            ),
            False,
        )

    def test_annotateQuerysetWithHasAbcdAttendanceAtDate_lessDeleteThanCreateEntries_annotatesTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        reference_datetime = timezone.now()

        for _ in range(2):
            create_attendance_template_log_entry_in_the_past(
                CreateShiftAttendanceTemplateLogEntry, tapir_user, reference_datetime
            )
        create_attendance_template_log_entry_in_the_past(
            DeleteShiftAttendanceTemplateLogEntry, tapir_user, reference_datetime
        )

        queryset = ShiftAttendanceModeService._annotate_queryset_with_has_abcd_attendance_at_datetime(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                ShiftAttendanceModeService.ANNOTATION_HAS_ABCD_ATTENDANCE_AT_DATE,
            ),
            True,
        )

    def test_annotateShiftUserDataQuerysetWithAttendanceModeAtDatetime_userIsFrozen_annotatesFrozen(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = True
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()

        queryset = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE,
            ),
            ShiftAttendanceMode.FROZEN,
        )

    def test_annotateShiftUserDataQuerysetWithAttendanceModeAtDatetime_userHasAbcdShift_annotatesRegular(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = False
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()
        create_attendance_template_log_entry_in_the_past(
            CreateShiftAttendanceTemplateLogEntry, tapir_user, reference_datetime
        )

        queryset = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE,
            ),
            ShiftAttendanceMode.REGULAR,
        )

    def test_annotateShiftUserDataQuerysetWithAttendanceModeAtDatetime_userHasNoAbcdShift_annotatesFyling(
        self,
    ):
        tapir_user: TapirUser = TapirUserFactory.create()
        tapir_user.shift_user_data.is_frozen = False
        tapir_user.shift_user_data.save()
        reference_datetime = timezone.now()

        queryset = ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
            ShiftUserData.objects.all(), reference_datetime
        )

        shift_user_data = queryset.first()
        self.assertEqual(
            getattr(
                shift_user_data,
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE,
            ),
            ShiftAttendanceMode.FLYING,
        )

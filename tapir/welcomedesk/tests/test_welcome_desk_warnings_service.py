import datetime
from unittest.mock import patch, Mock

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import (
    ShiftAttendanceMode,
    ShiftAttendanceTemplate,
    ShiftExemption,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.welcomedesk.services.welcome_desk_warnings_service import (
    WelcomeDeskWarningsService,
)


class TestWelcomeDeskWarningsService(TapirFactoryTestBase):

    def test_shouldShowWelcomeSessionWarning_memberWentToWelcomeSession_returnsFalse(
        self,
    ):
        share_owner = ShareOwnerFactory.build(attended_welcome_session=True)
        self.assertFalse(
            WelcomeDeskWarningsService.should_show_welcome_session_warning(share_owner)
        )

    def test_shouldShowWelcomeSessionWarning_memberDidntGoToWelcomeSession_returnsTrue(
        self,
    ):
        share_owner = ShareOwnerFactory.build(attended_welcome_session=False)
        self.assertTrue(
            WelcomeDeskWarningsService.should_show_welcome_session_warning(share_owner)
        )

    def test_shouldShowAbcdShiftRegistrationWarning_memberHasNoAccount_returnsFalse(
        self,
    ):
        share_owner = ShareOwnerFactory.build()
        self.assertFalse(
            WelcomeDeskWarningsService.should_show_abcd_shift_registration_warning(
                share_owner
            )
        )

    def test_shouldShowAbcdShiftRegistrationWarning_memberIsFlying_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        self.assertFalse(
            WelcomeDeskWarningsService.should_show_abcd_shift_registration_warning(
                tapir_user.share_owner
            )
        )

    def test_shouldShowAbcdShiftRegistrationWarning_memberIsRegisteredToAnAbcdShift_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        shift_template = ShiftTemplateFactory.create()
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=shift_template.slot_templates.first()
        )
        self.assertFalse(
            WelcomeDeskWarningsService.should_show_abcd_shift_registration_warning(
                tapir_user.share_owner
            )
        )

    def test_shouldShowAbcdShiftRegistrationWarning_memberHasAnExemption_returnsFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        ShiftExemption.objects.create(
            shift_user_data=tapir_user.shift_user_data,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
            end_date=None,
        )
        self.assertFalse(
            WelcomeDeskWarningsService.should_show_abcd_shift_registration_warning(
                tapir_user.share_owner
            )
        )

    def test_shouldShowAbcdShiftRegistrationWarning_memberIsNotRegisteredToAnAbcdShift_returnsTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create()
        tapir_user.shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        self.assertTrue(
            WelcomeDeskWarningsService.should_show_abcd_shift_registration_warning(
                tapir_user.share_owner
            )
        )

    @patch.object(
        WelcomeDeskWarningsService, "should_show_abcd_shift_registration_warning"
    )
    @patch.object(WelcomeDeskWarningsService, "should_show_welcome_session_warning")
    def test_buildWarnings_default_callsAllChecks(
        self,
        mock_should_show_welcome_session_warning: Mock,
        mock_should_show_abcd_shift_registration_warning: Mock,
    ):
        share_owner = ShareOwnerFactory.build()
        request_user = TapirUserFactory.create()
        mock_should_show_welcome_session_warning.return_value = True
        mock_should_show_abcd_shift_registration_warning.return_value = True

        warnings = WelcomeDeskWarningsService.build_warnings(share_owner, request_user)

        self.assertEqual(2, len(warnings))
        mock_should_show_welcome_session_warning.assert_called_once_with(
            share_owner=share_owner
        )
        mock_should_show_abcd_shift_registration_warning.assert_called_once_with(
            share_owner=share_owner
        )

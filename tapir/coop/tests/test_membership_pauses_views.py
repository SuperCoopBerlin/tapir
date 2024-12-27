import datetime

from django.urls import reverse

from tapir.accounts.models import TapirUser
from tapir.coop.models import (
    MembershipPauseCreatedLogEntry,
    MembershipPause,
    MembershipPauseUpdatedLogEntry,
)
from tapir.coop.tests.factories import ShareOwnerFactory, MembershipPauseFactory
from tapir.shifts.models import (
    ShiftAttendanceTemplate,
    ShiftAttendance,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory, ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMembershipPauseViews(TapirFactoryTestBase):
    CREATE_VIEW = "coop:membership_pause_create"
    EDIT_VIEW = "coop:membership_pause_edit"
    LIST_VIEW = "coop:membership_pauses"

    def test_createPause_default_logCreated(self):
        self.login_as_member_office_user()
        self.assertEqual(0, MembershipPauseCreatedLogEntry.objects.count())
        self.assertEqual(0, MembershipPause.objects.count())

        response = self.client.post(
            reverse(self.CREATE_VIEW),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "test description",
                "share_owner": ShareOwnerFactory.create().id,
            },
        )

        self.assertRedirects(response, reverse(self.LIST_VIEW))
        self.assertEqual(1, MembershipPause.objects.count())
        self.assertEqual(1, MembershipPauseCreatedLogEntry.objects.count())

    def test_createPause_default_shiftAttendanceTemplateGetsDeleted(self):
        tapir_user = self.login_as_member_office_user()
        shift_template = ShiftTemplateFactory.create()
        ShiftAttendanceTemplate.objects.create(
            user=tapir_user, slot_template=shift_template.slot_templates.first()
        )
        self.assertEqual(1, ShiftAttendanceTemplate.objects.count())

        response = self.client.post(
            reverse(self.CREATE_VIEW),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "description": "test description",
                "share_owner": tapir_user.share_owner.id,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse(self.LIST_VIEW))
        self.assertEqual(0, ShiftAttendanceTemplate.objects.count())
        self.assertEqual(1, DeleteShiftAttendanceTemplateLogEntry.objects.count())

    def test_createPause_default_shiftAttendancesDuringThePauseGetCancelled(self):
        tapir_user = self.login_as_member_office_user()

        attendance_before_pause = self.create_attendance(
            tapir_user, datetime.datetime(year=2020, month=5, day=1)
        )
        attendance_during_pause = self.create_attendance(
            tapir_user, datetime.datetime(year=2020, month=6, day=1)
        )
        attendance_after_pause = self.create_attendance(
            tapir_user, datetime.datetime(year=2020, month=7, day=1)
        )

        response = self.client.post(
            reverse(self.CREATE_VIEW),
            {
                "start_date": datetime.date(year=2020, month=5, day=15),
                "end_date": datetime.date(year=2020, month=6, day=15),
                "description": "test description",
                "share_owner": tapir_user.share_owner.id,
            },
        )

        self.assertRedirects(response, reverse(self.LIST_VIEW))
        attendance_before_pause.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.PENDING, attendance_before_pause.state)
        attendance_during_pause.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.CANCELLED, attendance_during_pause.state)
        attendance_after_pause.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.PENDING, attendance_after_pause.state)

    def test_createPause_loggedInAsNormalMember_returns403(self):
        self.login_as_normal_user()

        response = self.client.post(
            reverse(self.CREATE_VIEW),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "test description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(0, MembershipPauseCreatedLogEntry.objects.count())
        self.assertEqual(0, MembershipPause.objects.count())

    def test_editPause_default_logCreated(self):
        self.login_as_member_office_user()
        pause = MembershipPauseFactory.create(description="Start description")
        self.assertEqual(0, MembershipPauseUpdatedLogEntry.objects.count())

        response = self.client.post(
            reverse(self.EDIT_VIEW, args=[pause.id]),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "End description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse(self.LIST_VIEW))
        self.assertEqual(1, MembershipPauseUpdatedLogEntry.objects.count())
        pause.refresh_from_db()
        self.assertEqual(pause.description, "End description")

    def test_editPause_loggedInAsNormalMember_returns403(self):
        self.login_as_normal_user()
        pause = MembershipPauseFactory.create(description="Test description")

        response = self.client.post(
            reverse(self.EDIT_VIEW, args=[pause.id]),
            {
                "start_date": datetime.date(year=2023, month=1, day=5),
                "end_date": datetime.date(year=2024, month=2, day=6),
                "description": "rejected description",
                "share_owner": ShareOwnerFactory.create().id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(0, MembershipPauseUpdatedLogEntry.objects.count())
        self.assertEqual("Test description", pause.description)

    def test_editPause_default_shiftAttendancesDuringThePauseGetCancelled(self):
        tapir_user = self.login_as_member_office_user()
        pause = MembershipPauseFactory.create(share_owner=tapir_user.share_owner)

        attendance_before_pause = self.create_attendance(
            tapir_user, datetime.datetime(year=2020, month=5, day=1)
        )
        attendance_during_pause = self.create_attendance(
            tapir_user, datetime.datetime(year=2020, month=6, day=1)
        )
        attendance_after_pause = self.create_attendance(
            tapir_user, datetime.datetime(year=2020, month=7, day=1)
        )

        response = self.client.post(
            reverse(self.EDIT_VIEW, args=[pause.id]),
            {
                "start_date": datetime.date(year=2020, month=5, day=15),
                "end_date": datetime.date(year=2020, month=6, day=15),
                "description": "Test",
                "share_owner": tapir_user.share_owner.id,
            },
        )

        self.assertRedirects(response, reverse(self.LIST_VIEW))
        attendance_before_pause.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.PENDING, attendance_before_pause.state)
        attendance_during_pause.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.CANCELLED, attendance_during_pause.state)
        attendance_after_pause.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.PENDING, attendance_after_pause.state)

    def test_pauseList_viewerIsInMemberOffice_canSeeAllPauses(self):
        logged_in_user = self.login_as_member_office_user()
        pauses = {
            MembershipPauseFactory.create(share_owner=logged_in_user.share_owner),
            MembershipPauseFactory.create(),
        }

        response = self.client.get(reverse(self.LIST_VIEW))
        self.assertEqual(200, response.status_code)
        self.assertEqual(set(response.context["object_list"]), pauses)

    def test_pauseList_viewerIsNotMemberOffice_canOnlySeeOwnPauses(self):
        logged_in_user = self.login_as_normal_user()
        pause_of_logged_in_user = MembershipPauseFactory.create(
            share_owner=logged_in_user.share_owner
        )
        MembershipPauseFactory.create()  # pause of another member

        response = self.client.get(reverse(self.LIST_VIEW))
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            set(response.context["object_list"]), {pause_of_logged_in_user}
        )

    @staticmethod
    def create_attendance(tapir_user: TapirUser, start_time: datetime.datetime):
        return ShiftAttendance.objects.create(
            user=tapir_user,
            slot=ShiftFactory.create(start_time=start_time).slots.first(),
        )

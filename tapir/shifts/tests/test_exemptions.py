import datetime
from http import HTTPStatus

from django.urls import reverse
from django.utils import translation, timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import (
    ShiftExemption,
    ShiftAttendance,
    ShiftAttendanceTemplate,
    CreateExemptionLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory, ShiftFactory
from tapir.shifts.tests.utils import register_user_to_shift_template
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestExemptions(TapirFactoryTestBase):
    FIRST_CYCLE_START_DATE = datetime.date(day=18, month=1, year=2021)
    SECOND_CYCLE_START_DATE = datetime.date(day=15, month=2, year=2021)

    VIEW_NAME_EDIT_SHIFT_EXEMPTION = "shifts:edit_shift_exemption"
    VIEW_NAME_SHIFT_EXEMPTION_LIST = "shifts:shift_exemption_list"

    def test_no_exemption(self):
        user = TapirUserFactory.create()
        self.assertFalse(
            user.shift_user_data.is_currently_exempted_from_shifts(),
            "A newly created user should not be exempted from shifts.",
        )

    def test_active_exemption(self):
        user = TapirUserFactory.create()
        self.create_exemption(
            user=user,
            start_date=timezone.now().date() - datetime.timedelta(days=7),
            end_date=timezone.now().date() + datetime.timedelta(days=7),
        )

        self.assertTrue(
            user.shift_user_data.is_currently_exempted_from_shifts(),
            "The user should be exempted for today.",
        )
        self.assertTrue(
            user.shift_user_data.is_currently_exempted_from_shifts(
                timezone.now().date() + datetime.timedelta(days=2)
            ),
            "The user should be exempted for in two days from now.",
        )

    def test_past_exemption(self):
        user = TapirUserFactory.create()
        self.create_exemption(
            user=user,
            start_date=timezone.now().date() - datetime.timedelta(days=120),
            end_date=timezone.now().date() - datetime.timedelta(days=30),
        )

        self.assertFalse(
            user.shift_user_data.is_currently_exempted_from_shifts(
                timezone.now().date()
            ),
            "The exemption is finished, the user should not be exempted today.",
        )

    def test_past_exemption_no_end_date(self):
        user = TapirUserFactory.create()
        self.create_exemption(
            user=user,
            start_date=timezone.now().date() - datetime.timedelta(days=120),
            end_date=None,
        )

        self.assertTrue(
            user.shift_user_data.is_currently_exempted_from_shifts(
                timezone.now().date()
            ),
            "The exemption has no end, the user should be exempted.",
        )

    def test_future_exemption(self):
        user = TapirUserFactory.create()
        self.create_exemption(
            user=user,
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=None,
        )

        self.assertFalse(
            user.shift_user_data.is_currently_exempted_from_shifts(
                timezone.now().date()
            ),
            "The exemption is not started yet, the user should not be exempted today.",
        )

    def test_attendance_cancelled_during_short_exemption(self):
        user = TapirUserFactory.create()
        shift_template = ShiftTemplateFactory.create()
        shift_cancelled = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        shift_kept = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=20)
        )
        self.login_as_member_office_user()
        register_user_to_shift_template(self.client, user, shift_template)

        post_data = {
            "start_date": timezone.now().date() - datetime.timedelta(days=10),
            "end_date": timezone.now().date() + datetime.timedelta(days=10),
            "description": "A test exemption",
        }
        response = self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            post_data,
        )
        response_content = response.content.decode()
        self.assertIn(
            "confirm_cancelled_attendances",
            response_content,
            "There should be a warning about the attendance that will be cancelled.",
        )
        self.assertIn(
            shift_cancelled.slots.first().get_display_name(),
            response_content,
            "The cancelled slot name should be part of the warning.",
        )

        post_data["confirm_cancelled_attendances"] = True
        self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            post_data,
        )

        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift_cancelled).state,
            ShiftAttendance.State.CANCELLED,
            "The shift is within the exemption, the attendance should have been cancelled.",
        )
        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift_kept).state,
            ShiftAttendance.State.PENDING,
            "The shift is outside the exemption, the attendance should have stayed the same.",
        )
        self.assertTrue(
            ShiftAttendanceTemplate.objects.filter(
                user=user, slot_template__shift_template=shift_template
            ).exists(),
            "The exemption is short, the user should not have lost it's ABCD slot.",
        )

    def test_attendance_cancelled_during_long_exemption(self):
        self.do_long_exemption_test(
            end_date=timezone.now().date() + datetime.timedelta(days=365)
        )

    def test_attendance_cancelled_during_infinite_exemption(self):
        self.do_long_exemption_test(end_date=None)

    def do_long_exemption_test(self, end_date):
        language = "en"
        user = TapirUserFactory.create(is_in_member_office=False)
        shift_template = ShiftTemplateFactory.create()
        shift_kept = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        shift_cancelled = shift_template.create_shift(
            start_date=timezone.now().date() + datetime.timedelta(days=20)
        )
        member_office_user = TapirUserFactory.create(
            preferred_language=language, is_in_member_office=True
        )
        self.login_as_user(member_office_user)
        register_user_to_shift_template(self.client, user, shift_template)

        post_data = {
            "start_date": timezone.now().date() + datetime.timedelta(days=10),
            "end_date": end_date if end_date else "",
            "description": "A test exemption",
        }
        response = self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            post_data,
        )
        response_content = response.content.decode()
        self.assertIn(
            "confirm_cancelled_attendances",
            response_content,
            "There should be a warning about the attendance that will get cancelled.",
        )
        with translation.override(member_office_user.preferred_language):
            self.assertIn(
                shift_cancelled.slots.first().get_display_name(),
                response_content,
                "The cancelled slot name should be part of the warning.",
            )
        with translation.override(member_office_user.preferred_language):
            self.assertNotIn(
                shift_kept.slots.first().get_display_name(),
                response_content,
                "That shift is not affected, the slot name should not be in the list.",
            )
        self.assertIn(
            "confirm_cancelled_abcd_attendances",
            response_content,
            "There should be a warning about the attendance template that will get cancelled.",
        )
        with translation.override(member_office_user.preferred_language):
            self.assertIn(
                shift_template.slot_templates.first().get_display_name(),
                response_content,
                "The cancelled slot template name should be part of the warning.",
            )

        post_data["confirm_cancelled_attendances"] = True
        post_data["confirm_cancelled_abcd_attendances"] = True
        self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            post_data,
        )

        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift_cancelled).state,
            ShiftAttendance.State.CANCELLED,
            "The shift is within the exemption, the attendance should have been cancelled.",
        )
        self.assertEqual(
            ShiftAttendance.objects.get(user=user, slot__shift=shift_kept).state,
            ShiftAttendance.State.PENDING,
            "The shift is outside the exemption, the attendance should have been kept.",
        )
        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(
                user=user, slot_template__shift_template=shift_template
            ).exists(),
            "The exemption is long, the user should have lost it's ABCD slot.",
        )

    def create_exemption(self, user, start_date, end_date):
        self.login_as_member_office_user()
        self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            {
                "start_date": start_date,
                "end_date": end_date if end_date else "",
                "description": "A test exemption",
            },
        )

        self.assertEqual(
            ShiftExemption.objects.filter(shift_user_data=user.shift_user_data).count(),
            1,
            "The exemption should have been created. The tests also assume that the user has no other exemption.",
        )

    def test_creates_log_entry(self):
        user = TapirUserFactory.create()
        start_date = timezone.now().date() + datetime.timedelta(days=30)
        end_date = timezone.now().date() + datetime.timedelta(days=50)
        self.assertEqual(CreateExemptionLogEntry.objects.count(), 0)

        actor = self.login_as_member_office_user()
        response = self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            {
                "start_date": start_date,
                "end_date": end_date if end_date else "",
                "description": "A test exemption",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CreateExemptionLogEntry.objects.count(), 1)
        log_entry = CreateExemptionLogEntry.objects.first()
        self.assertEqual(log_entry.start_date, start_date)
        self.assertEqual(log_entry.end_date, end_date)
        self.assertEqual(log_entry.actor, actor)
        self.assertEqual(log_entry.user, user)

    def test_edit_shift_exemption_requires_member_office_access(self):
        user = self.login_as_normal_user()
        shift_template = ShiftTemplateFactory.create()
        ShiftAttendanceTemplate.objects.create(
            user=user, slot_template=shift_template.slot_templates.first()
        )
        exemption = ShiftExemption.objects.create(
            shift_user_data=user.shift_user_data,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=3),
            description="Lorem ipsum",
        )

        post_data = {
            "start_date": exemption.start_date,
            "end_date": timezone.now().date() + datetime.timedelta(days=365),
            "description": "A test exemption",
        }
        self._assert_no_access_to_exemption_creation(exemption, post_data)

        self.login_as_shift_manager()
        self._assert_no_access_to_exemption_creation(exemption, post_data)

    def _assert_no_access_to_exemption_creation(self, exemption, post_data):
        response = self.client.post(
            reverse(self.VIEW_NAME_EDIT_SHIFT_EXEMPTION, args=[exemption.pk]),
            post_data,
            follow=True,
        )

        self.assertEqual(
            response.status_code,
            403,
            "A user that is not in the member office should not have access to shift slot creation.",
        )

    def test_edit_exemption_cancels_abcd_shift(self):
        user = TapirUserFactory.create(is_in_member_office=False)
        shift_template = ShiftTemplateFactory.create()
        ShiftAttendanceTemplate.objects.create(
            user=user, slot_template=shift_template.slot_templates.first()
        )
        exemption = ShiftExemption.objects.create(
            shift_user_data=user.shift_user_data,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=3),
            description="dolor sit amet",
        )

        self.login_as_member_office_user()
        post_data = {
            "start_date": exemption.start_date,
            "end_date": timezone.now().date() + datetime.timedelta(days=365),
            "description": "A test exemption",
            "confirm_cancelled_abcd_attendances": True,
        }
        response = self.client.post(
            reverse(self.VIEW_NAME_EDIT_SHIFT_EXEMPTION, args=[exemption.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertFalse(
            ShiftAttendanceTemplate.objects.filter(
                user=user, slot_template__shift_template=shift_template
            ).exists(),
            "The exemption got edited to something longer than the threshold, the attendance should be cancelled",
        )

    def test_edit_exemption_cancels_single_shift(self):
        user = TapirUserFactory.create(is_in_member_office=False)
        shift_1 = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=1)
        )
        attendance_1 = ShiftAttendance.objects.create(
            user=user, slot=shift_1.slots.first()
        )

        shift_2 = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=10)
        )
        attendance_2 = ShiftAttendance.objects.create(
            user=user, slot=shift_2.slots.first()
        )

        shift_3 = ShiftFactory.create(
            start_time=timezone.now() + datetime.timedelta(days=20)
        )
        attendance_3 = ShiftAttendance.objects.create(
            user=user, slot=shift_3.slots.first()
        )

        exemption = ShiftExemption.objects.create(
            shift_user_data=user.shift_user_data,
            start_date=timezone.now().date() + datetime.timedelta(days=3),
            end_date=timezone.now().date() + datetime.timedelta(days=8),
            description="consectetur adipiscing elit",
        )

        self.login_as_member_office_user()
        post_data = {
            "start_date": exemption.start_date,
            "end_date": timezone.now().date() + datetime.timedelta(days=15),
            "description": "A test exemption",
            "confirm_cancelled_attendances": True,
        }
        response = self.client.post(
            reverse(self.VIEW_NAME_EDIT_SHIFT_EXEMPTION, args=[exemption.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(ShiftAttendance.State.PENDING, attendance_1.state)
        attendance_1.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.PENDING, attendance_1.state)

        self.assertEqual(ShiftAttendance.State.PENDING, attendance_2.state)
        attendance_2.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.CANCELLED, attendance_2.state)

        self.assertEqual(ShiftAttendance.State.PENDING, attendance_3.state)
        attendance_3.refresh_from_db()
        self.assertEqual(ShiftAttendance.State.PENDING, attendance_3.state)

    def test_invalid_attendances_are_not_affected_by_exemptions(self):
        tapir_user: TapirUser = TapirUserFactory.create()

        for state in ShiftAttendance.State:
            shift = ShiftFactory.create(start_time=timezone.now())
            ShiftAttendance.objects.create(
                user=tapir_user,
                slot=shift.slots.first(),
                state=state,
            )

        attendances = ShiftExemption.get_attendances_cancelled_by_exemption(
            user=tapir_user,
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=None,
        )
        self.assertEqual(2, attendances.count())
        self.assertEqual(
            1, attendances.filter(state=ShiftAttendance.State.PENDING).count()
        )
        self.assertEqual(
            1,
            attendances.filter(
                state=ShiftAttendance.State.LOOKING_FOR_STAND_IN
            ).count(),
        )

    def test_normal_member_can_only_see_own_exemptions(self):
        other_user = TapirUserFactory.create()
        ShiftExemption.objects.create(
            shift_user_data=other_user.shift_user_data,
            start_date=datetime.date(day=1, month=1, year=2020),
            end_date=datetime.date(day=12, month=3, year=2022),
        )

        logged_in_user = self.login_as_normal_user()
        ShiftExemption.objects.create(
            shift_user_data=other_user.shift_user_data,
            start_date=datetime.date(day=1, month=1, year=2020),
            end_date=datetime.date(day=12, month=3, year=2022),
        )

        response = self.client.get(reverse(self.VIEW_NAME_SHIFT_EXEMPTION_LIST))
        self.assertEqual(200, response.status_code)
        response_content = response.content.decode()
        self.assertNotIn(other_user.last_name, response_content)
        self.assertIn(logged_in_user.last_name, response_content)

    def test_shift_manager_can_only_see_own_exemptions(self):
        other_user = TapirUserFactory.create()
        ShiftExemption.objects.create(
            shift_user_data=other_user.shift_user_data,
            start_date=datetime.date(day=1, month=1, year=2020),
            end_date=datetime.date(day=12, month=3, year=2022),
        )

        logged_in_user = self.login_as_shift_manager()
        ShiftExemption.objects.create(
            shift_user_data=other_user.shift_user_data,
            start_date=datetime.date(day=1, month=1, year=2020),
            end_date=datetime.date(day=12, month=3, year=2022),
        )

        response = self.client.get(reverse(self.VIEW_NAME_SHIFT_EXEMPTION_LIST))
        self.assertEqual(200, response.status_code)
        response_content = response.content.decode()
        self.assertNotIn(other_user.last_name, response_content)
        self.assertIn(logged_in_user.last_name, response_content)

    def test_member_office_can_see_all_exemptions(self):
        other_user_1 = TapirUserFactory.create()
        ShiftExemption.objects.create(
            shift_user_data=other_user_1.shift_user_data,
            start_date=datetime.date(day=1, month=1, year=2020),
            end_date=datetime.date(day=12, month=3, year=2022),
        )

        other_user_2 = TapirUserFactory.create()
        ShiftExemption.objects.create(
            shift_user_data=other_user_2.shift_user_data,
            start_date=datetime.date(day=1, month=1, year=2020),
            end_date=datetime.date(day=12, month=3, year=2022),
        )

        self.login_as_member_office_user()
        response = self.client.get(reverse(self.VIEW_NAME_SHIFT_EXEMPTION_LIST))
        self.assertEqual(200, response.status_code)
        response_content = response.content.decode()
        self.assertIn(other_user_1.last_name, response_content)
        self.assertIn(other_user_2.last_name, response_content)

    def test_createShiftExemptionView_longExemptionCreated_attendanceTemplateDeleted(
        self,
    ):
        self.login_as_member_office_user()
        user = TapirUserFactory.create()
        shift_template = ShiftTemplateFactory.create()
        register_user_to_shift_template(self.client, user, shift_template)
        self.assertEqual(1, ShiftAttendanceTemplate.objects.count())

        post_data = {
            "start_date": timezone.now().date() - datetime.timedelta(days=10),
            "end_date": timezone.now().date() + datetime.timedelta(days=365),
            "description": "A test exemption",
            "confirm_cancelled_abcd_attendances": True,
        }
        response = self.client.post(
            reverse("shifts:create_shift_exemption", args=[user.shift_user_data.pk]),
            post_data,
            follow=True,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual(1, ShiftExemption.objects.count())
        self.assertEqual(0, ShiftAttendanceTemplate.objects.count())
        self.assertEqual(1, DeleteShiftAttendanceTemplateLogEntry.objects.count())

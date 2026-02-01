import datetime

from django.urls import reverse
from django.utils import timezone
from tapir.shifts.models import (
    ShiftTemplate,
    ShiftTemplateGroup,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.shortcuts import get_monday
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShiftTemplateEdit(TapirFactoryTestBase):
    SHIFT_TEMPLATE_EDIT_VIEW = "shifts:shift_template_edit"

    def test_after_call_future_shifts_are_updated(self):
        self.login_as_member_office_user()

        for name in ["A", "B"]:
            ShiftTemplateGroup.objects.create(name=name)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_time=datetime.time(hour=6, minute=0),
            end_time=datetime.time(hour=13, minute=0),
            num_required_attendances=3,
            weekday=0,
        )
        shift_template.group = ShiftTemplateGroup.objects.get(name="A")
        shift_template.save()

        shift_1 = shift_template.create_shift_if_necessary(
            start_date=timezone.now().date() + datetime.timedelta(days=10)
        )
        shift_2 = shift_template.create_shift_if_necessary(
            start_date=timezone.now().date() + datetime.timedelta(days=30)
        )

        name = "Updated name"
        description = "Updated description"
        start_time = datetime.time(hour=11, minute=30)
        end_time = datetime.time(hour=13, minute=45)
        num_required_attendances = 4
        weekday = 1
        group = ShiftTemplateGroup.objects.get(name="B")

        response = self.client.post(
            reverse(self.SHIFT_TEMPLATE_EDIT_VIEW, args=[shift_template.pk]),
            {
                "name": name,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "num_required_attendances": num_required_attendances,
                "group": group.id,
                "weekday": weekday,
                "check_update_future_shifts": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        for shift in [shift_1, shift_2]:
            shift.refresh_from_db()
            self.assertEqual(name, shift.name)
            self.assertEqual(description, shift.description)
            self.assertEqual(start_time, timezone.localtime(shift.start_time).time())
            self.assertEqual(end_time, timezone.localtime(shift.end_time).time())
            self.assertEqual(weekday, shift.start_time.weekday())
            self.assertEqual(num_required_attendances, shift.num_required_attendances)

    def test_not_accessible_for_normal_users(self):
        self.login_as_normal_user()

        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            start_time=datetime.time(hour=6, minute=0),
            end_time=datetime.time(hour=13, minute=0),
            num_required_attendances=3,
            weekday=0,
        )

        response = self.client.post(
            reverse(self.SHIFT_TEMPLATE_EDIT_VIEW, args=[shift_template.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_after_call_past_shifts_are_not_updated(self):
        self.login_as_member_office_user()

        for name in ["A", "B"]:
            ShiftTemplateGroup.objects.create(name=name)
        shift_template: ShiftTemplate = ShiftTemplateFactory.create(
            name="Name before",
            description="Description before",
            start_time=datetime.time(hour=10, minute=0),
            end_time=datetime.time(hour=13, minute=0),
            num_required_attendances=3,
            weekday=0,
        )
        shift_template.group = ShiftTemplateGroup.objects.get(name="A")
        shift_template.save()

        shift = shift_template.create_shift_if_necessary(
            start_date=get_monday(timezone.now().date() - datetime.timedelta(days=10))
        )

        response = self.client.post(
            reverse(self.SHIFT_TEMPLATE_EDIT_VIEW, args=[shift_template.pk]),
            {
                "name": "Name after",
                "description": "Description after",
                "start_time": datetime.time(hour=11, minute=30),
                "end_time": datetime.time(hour=13, minute=45),
                "num_required_attendances": 4,
                "group": ShiftTemplateGroup.objects.get(name="B").id,
                "weekday": 1,
                "check_update_future_shifts": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        shift_template.refresh_from_db()
        self.assertEqual("Name after", shift_template.name)

        shift.refresh_from_db()
        self.assertEqual("Name before", shift.name)
        self.assertEqual("Description before", shift.description)
        self.assertEqual(
            datetime.time(hour=10, minute=0),
            timezone.localtime(shift.start_time).time(),
        )
        self.assertEqual(
            datetime.time(hour=13, minute=0), timezone.localtime(shift.end_time).time()
        )
        self.assertEqual(0, shift.start_time.weekday())
        self.assertEqual(3, shift.num_required_attendances)

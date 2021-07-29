import datetime
import json
import os
import pathlib
import random

from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, ShareOwnership, DraftUser
from tapir.log.models import LogEntry
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftTemplateGroup,
    ShiftAttendanceTemplate,
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftAccountEntry,
    ShiftUserData,
    ShiftSlotTemplate,
    ShiftSlot,
    ShiftUserCapability,
)
from tapir.utils.json_user import JsonUser
from tapir.utils.models import copy_user_info


def delete_templates():
    ShiftAttendanceTemplate.objects.all().delete()
    ShiftTemplate.objects.all().delete()


def populate_shifts():
    for delta in range(-7, 7):
        date = datetime.date.today() - datetime.timedelta(days=delta)
        morning = datetime.datetime.combine(
            date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
        )
        noon = datetime.datetime.combine(
            date, datetime.time(hour=12, tzinfo=datetime.timezone.utc)
        )
        evening = datetime.datetime.combine(
            date, datetime.time(hour=16, tzinfo=datetime.timezone.utc)
        )

        shift = Shift.objects.get_or_create(
            name="Cashier morning",
            start_time=morning,
            end_time=noon,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift, optional=False)

        shift = Shift.objects.get_or_create(
            name="Cashier afternoon",
            start_time=noon,
            end_time=evening,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift, optional=False)

        shift = Shift.objects.get_or_create(
            name="Storage morning",
            start_time=morning,
            end_time=noon,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift, optional=False)

        shift = Shift.objects.get_or_create(
            name="Storage afternoon",
            start_time=noon,
            end_time=evening,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift, optional=False)

    print("Populated shift templates for today")


def populate_user_shifts(user_id):
    user = TapirUser.objects.get(pk=user_id)

    date = datetime.date.today() - datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name="Cashier morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.DONE
    )

    date = datetime.date.today() - datetime.timedelta(days=2)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name="Storage morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift,
        user=user,
        state=ShiftAttendance.State.MISSED_EXCUSED,
        excused_reason="Was sick",
    )

    date = datetime.date.today() + datetime.timedelta(days=1)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name="Cashier morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.CANCELLED
    )

    start_time = datetime.datetime.combine(
        date, datetime.time(hour=12, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name="Cashier afternoon", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.PENDING
    )

    date = datetime.date.today() + datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=12, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name="Storage afternoon", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.PENDING
    )

    print("Populated user " + user.username + "(id=" + str(user_id) + ") shifts")


def populate_template_groups():
    ShiftTemplateGroup.objects.all().delete()
    for week in ["A", "B", "C", "D"]:
        ShiftTemplateGroup.objects.get_or_create(name="Week " + week)

    print("Populated template groups")


def populate_users():
    # Users generated with https://randomuser.me
    print("Creating 200 users, this may take a while")

    path_to_json_file = os.path.join(
        pathlib.Path(__file__).parent.absolute(), "test_users.json"
    )
    file = open(path_to_json_file, encoding="UTF-8")
    json_string = file.read()
    file.close()

    parsed_users = json.loads(json_string)["results"]
    for index, parsed_user in enumerate(parsed_users[:200]):
        if index % 50 == 0:
            print(str(index) + "/200")
        json_user = JsonUser(parsed_user)

        tapir_user = TapirUser.objects.create(
            username=json_user.get_username(),
        )
        copy_user_info(json_user, tapir_user)
        tapir_user.is_staff = False
        tapir_user.is_active = True
        tapir_user.save()

        share_owner = ShareOwner.objects.create(
            is_company=False,
            user=tapir_user,
        )
        share_owner.blank_info_fields()
        share_owner.is_investing = tapir_user.pk % 7 == 0
        share_owner.from_startnext = tapir_user.pk % 5 == 0
        share_owner.ratenzahlung = tapir_user.pk % 10 == 0
        share_owner.save()

        ShareOwnership.objects.create(
            owner=share_owner,
            start_date=datetime.date.today(),
        )

        if not ShiftAttendanceTemplate.objects.filter(user=tapir_user).exists():
            for _ in range(10):
                template: ShiftTemplate = random.choice(ShiftTemplate.objects.all())
                free_slots = template.slot_templates.filter(
                    attendance_template__isnull=True
                )
                if free_slots.exists():
                    for free_slot in free_slots:
                        # Attend the first one fit for this user.
                        if free_slot.user_can_attend(tapir_user):
                            ShiftAttendanceTemplate.objects.create(
                                user=tapir_user, slot_template=free_slot
                            )
                            break
                template.update_future_shift_attendances()
                break
    print("Created fake uses")


def populate_shift_templates():
    if ShiftTemplateGroup.objects.count() < 4:
        populate_template_groups()

    names = ["Supermarket"]
    start_hours = [9, 12, 15]
    for weekday in WEEKDAY_CHOICES[:-1]:
        for template_group in ShiftTemplateGroup.objects.all():
            for name in names:
                for start_hour in start_hours:
                    start_time = datetime.time(
                        hour=start_hour, tzinfo=timezone.localtime().tzinfo
                    )
                    end_time = datetime.time(
                        hour=start_hour + 3, tzinfo=timezone.localtime().tzinfo
                    )
                    shift_template = ShiftTemplate.objects.create(
                        name=name,
                        group=template_group,
                        weekday=weekday[0],
                        start_time=start_time,
                        end_time=end_time,
                    )

                    ShiftSlotTemplate.objects.create(
                        name="Shift Coordinator",
                        shift_template=shift_template,
                        required_capabilities=[ShiftUserCapability.SHIFT_COORDINATOR],
                        optional=False,
                    )
                    for _ in range(3):
                        ShiftSlotTemplate.objects.create(
                            shift_template=shift_template, optional=False
                        )
                    ShiftSlotTemplate.objects.create(
                        shift_template=shift_template, optional=True
                    )

    for weekday in [WEEKDAY_CHOICES[2], WEEKDAY_CHOICES[5]]:
        for template_group in ShiftTemplateGroup.objects.all():
            start_time = datetime.time(hour=18, tzinfo=timezone.localtime().tzinfo)
            end_time = datetime.time(hour=18 + 3, tzinfo=timezone.localtime().tzinfo)
            name = "Store cleaning"
            shift_template = ShiftTemplate.objects.create(
                name=name,
                group=template_group,
                weekday=weekday[0],
                start_time=start_time,
                end_time=end_time,
            )
            for _ in range(3):
                ShiftSlotTemplate.objects.create(
                    shift_template=shift_template, optional=False
                )

    for group_name in ["A", "C"]:
        start_time = datetime.time(hour=9, tzinfo=timezone.localtime().tzinfo)
        end_time = datetime.time(hour=9 + 3, tzinfo=timezone.localtime().tzinfo)
        name = "Inventory"
        template_group = ShiftTemplateGroup.objects.get(name="Week " + group_name)
        shift_template = ShiftTemplate.objects.create(
            name=name,
            group=template_group,
            weekday=WEEKDAY_CHOICES[6][0],
            start_time=start_time,
            end_time=end_time,
        )
        for _ in range(3):
            ShiftSlotTemplate.objects.create(
                shift_template=shift_template, optional=False
            )

    for group_name in ["B", "D"]:
        start_time = datetime.time(hour=9, tzinfo=timezone.localtime().tzinfo)
        end_time = datetime.time(hour=9 + 3, tzinfo=timezone.localtime().tzinfo)
        name = "Storage cleaning"
        template_group = ShiftTemplateGroup.objects.get(name="Week " + group_name)
        shift_template = ShiftTemplate.objects.create(
            name=name,
            group=template_group,
            weekday=WEEKDAY_CHOICES[6][0],
            start_time=start_time,
            end_time=end_time,
        )
        for _ in range(3):
            ShiftSlotTemplate.objects.create(
                shift_template=shift_template, optional=False
            )

    print("Populated shift templates")


def generate_shifts(print_progress=False):
    if print_progress:
        print("Generating shifts")
    start_day = datetime.date.today() - datetime.timedelta(days=20)
    while start_day.weekday() != 0:
        start_day = start_day + datetime.timedelta(days=1)

    groups = ShiftTemplateGroup.objects.all()
    for week in range(8):
        monday = start_day + datetime.timedelta(days=7 * week)
        if print_progress:
            print("Doing week from " + str(monday) + " " + str(week + 1) + "/8")
        groups[week % 4].create_shifts(monday)
    if print_progress:
        print("Generated shifts")


def clear_data():
    print("Clearing data...")
    LogEntry.objects.all().delete()
    ShiftAttendance.objects.all().delete()
    ShiftAccountEntry.objects.all().delete()
    Shift.objects.all().delete()
    ShiftAttendanceTemplate.objects.all().delete()
    ShiftTemplate.objects.all().delete()
    ShiftTemplateGroup.objects.all().delete()
    ShiftUserData.objects.all().delete()
    ShareOwnership.objects.all().delete()
    ShareOwner.objects.all().delete()
    DraftUser.objects.all().delete()
    TapirUser.objects.filter(is_staff=False).delete()
    print("Done")


def reset_all_test_data():
    random.seed("supercoop")
    clear_data()
    populate_template_groups()
    populate_shift_templates()
    generate_shifts(True)
    populate_users()

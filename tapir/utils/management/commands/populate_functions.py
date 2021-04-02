import json
import datetime
import random

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftTemplateGroup,
    ShiftAttendanceTemplate,
    ShiftTemplate,
    WEEKDAY_CHOICES,
)


def delete_templates():
    ShiftAttendanceTemplate.objects.all().delete()
    ShiftTemplate.objects.all().delete()


def populate_shifts():
    for delta in range(-7, 7):
        date = datetime.date.today() - datetime.timedelta(days=delta)
        morning = datetime.datetime.combine(date, datetime.time(hour=8))
        noon = datetime.datetime.combine(date, datetime.time(hour=12))
        evening = datetime.datetime.combine(date, datetime.time(hour=16))

        Shift.objects.get_or_create(
            name="Cashier morning",
            start_time=morning,
            end_time=noon,
            num_slots=4,
        )

        Shift.objects.get_or_create(
            name="Cashier afternoon",
            start_time=noon,
            end_time=evening,
            num_slots=4,
        )

        Shift.objects.get_or_create(
            name="Storage morning",
            start_time=morning,
            end_time=noon,
            num_slots=3,
        )

        Shift.objects.get_or_create(
            name="Storage afternoon",
            start_time=noon,
            end_time=evening,
            num_slots=3,
        )

    print("Populated shift templates for today")


def populate_user_shifts(request, user_id):
    user = TapirUser.objects.get(pk=user_id)

    date = datetime.date.today() - datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(date, datetime.time(hour=8))
    shift = Shift.objects.get(name="Cashier morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.DONE
    )

    date = datetime.date.today() - datetime.timedelta(days=2)
    start_time = datetime.datetime.combine(date, datetime.time(hour=8))
    shift = Shift.objects.get(name="Storage morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift,
        user=user,
        state=ShiftAttendance.State.MISSED_EXCUSED,
        excused_reason="Was sick",
    )

    date = datetime.date.today() + datetime.timedelta(days=1)
    start_time = datetime.datetime.combine(date, datetime.time(hour=8))
    shift = Shift.objects.get(name="Cashier morning", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.CANCELLED
    )

    start_time = datetime.datetime.combine(date, datetime.time(hour=12))
    shift = Shift.objects.get(name="Cashier afternoon", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.PENDING
    )

    date = datetime.date.today() + datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(date, datetime.time(hour=12))
    shift = Shift.objects.get(name="Storage afternoon", start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.PENDING
    )

    print("Populated user " + user.name + "(id=" + str(user_id) + ") shifts")


def populate_template_groups():
    ShiftTemplateGroup.objects.all().delete()
    for week in ["C", "B", "A", "D"]:
        ShiftTemplateGroup.objects.get_or_create(name="Week " + week)

    print("Populated template groups")


def populate_users():
    # Users generated with https://randomuser.me
    print("Creating 500 users, this may take a while")
    file = open("test_users.json")
    json_string = file.read()
    file.close()
    users = json.loads(json_string)["results"]
    for index, user in enumerate(users[:500]):
        if index % 50 == 0:
            print(str(index) + "/500")
        username: str = user["name"]["first"] + "_" + user["name"]["last"]
        username = username.lower()
        date_joined = user["registered"]["date"].replace("Z", "")
        date_joined = datetime.datetime.fromisoformat(date_joined)
        (tapir_user, _) = TapirUser.objects.get_or_create(
            username=username,
            first_name=user["name"]["first"],
            last_name=user["name"]["last"],
            email=user["email"],
            is_staff=False,
            is_active=True,
            date_joined=date_joined,
        )

        if ShiftAttendanceTemplate.objects.filter(user=tapir_user).count() > 0:
            continue
        for _ in range(10):
            template: ShiftTemplate = random.choice(ShiftTemplate.objects.all())
            attendances = ShiftAttendanceTemplate.objects.filter(
                shift_template=template
            )
            if attendances.count() == template.num_slots:
                continue
            ShiftAttendanceTemplate.objects.create(
                user=tapir_user, shift_template=template
            )
            template.generated_shifts
            break
    print("Created fake uses")


def populate_shift_templates():
    populate_template_groups()
    names = ["Organize the shop", "Cashier"]
    start_hours = [9, 12, 15]
    for weekday in WEEKDAY_CHOICES[:-1]:
        for template_group in ShiftTemplateGroup.objects.all():
            for name in names:
                for start_hour in start_hours:
                    start_time = datetime.time(hour=start_hour)
                    end_time = datetime.time(hour=start_hour + 3)
                    ShiftTemplate.objects.get_or_create(
                        name=name,
                        group=template_group,
                        weekday=weekday[0],
                        start_time=start_time,
                        end_time=end_time,
                        num_slots=4,
                    )

    for weekday in [WEEKDAY_CHOICES[2], WEEKDAY_CHOICES[5]]:
        for template_group in ShiftTemplateGroup.objects.all():
            start_time = datetime.time(hour=18)
            end_time = datetime.time(hour=18 + 3)
            name = "Store cleaning"
            ShiftTemplate.objects.get_or_create(
                name=name,
                group=template_group,
                weekday=weekday[0],
                start_time=start_time,
                end_time=end_time,
                num_slots=3,
            )

    for group_name in ["A", "C"]:
        start_time = datetime.time(hour=9)
        end_time = datetime.time(hour=9 + 3)
        name = "Inventory"
        template_group = ShiftTemplateGroup.objects.get(name="Week " + group_name)
        ShiftTemplate.objects.get_or_create(
            name=name,
            group=template_group,
            weekday=WEEKDAY_CHOICES[6][0],
            start_time=start_time,
            end_time=end_time,
            num_slots=3,
        )

    for group_name in ["B", "D"]:
        start_time = datetime.time(hour=9)
        end_time = datetime.time(hour=9 + 3)
        name = "Storage cleaning"
        template_group = ShiftTemplateGroup.objects.get(name="Week " + group_name)
        ShiftTemplate.objects.get_or_create(
            name=name,
            group=template_group,
            weekday=WEEKDAY_CHOICES[6][0],
            start_time=start_time,
            end_time=end_time,
            num_slots=3,
        )

    print("Populated shift templates")


def generate_shifts():
    print("Generating shifts")
    start_day = datetime.datetime.now() - datetime.timedelta(days=20)
    while start_day.weekday() != 0:
        start_day = start_day + datetime.timedelta(days=1)

    for week in range(8):
        monday = start_day + datetime.timedelta(days=7 * week)
        print("Doing week from " + str(monday) + " " + str(week + 1) + "/8")
        for group in ShiftTemplateGroup.objects.all():
            print("\t" + group.name)
            group.create_shifts(monday)
    print("Generated shifts")

import datetime
import json
import os
import pathlib
import random

from django.utils import timezone

from tapir.accounts.models import TapirUser, LdapGroup
from tapir.coop.models import (
    ShareOwner,
    ShareOwnership,
    DraftUser,
    IncomingPayment,
    NewMembershipsForAccountingRecap,
    ExtraSharesForAccountingRecap,
    MemberStatus,
)
from tapir.log.models import LogEntry
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftTemplateGroup,
    ShiftAttendanceTemplate,
    ShiftTemplate,
    ShiftAccountEntry,
    ShiftUserData,
    ShiftSlotTemplate,
    ShiftSlot,
    ShiftUserCapability,
    ShiftCycleEntry,
)
from tapir.statistics.models import ProcessedPurchaseFiles, PurchaseBasket
from tapir.utils.json_user import JsonUser
from tapir.utils.models import copy_user_info
from tapir.utils.shortcuts import get_monday, get_timezone_aware_datetime

SHIFT_NAME_CASHIER_MORNING = "Cashier morning"
SHIFT_NAME_CASHIER_AFTERNOON = "Cashier afternoon"
SHIFT_NAME_STORAGE_MORNING = "Storage morning"
SHIFT_NAME_STORAGE_AFTERNOON = "Storage afternoon"


def delete_templates():
    ShiftAttendanceTemplate.objects.all().delete()
    ShiftTemplate.objects.all().delete()


def generate_test_shifts():
    for delta in range(-7, 7):
        date = timezone.now().today() - datetime.timedelta(days=delta)
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
            name=SHIFT_NAME_CASHIER_MORNING,
            start_time=morning,
            end_time=noon,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift)

        shift = Shift.objects.get_or_create(
            name=SHIFT_NAME_CASHIER_AFTERNOON,
            start_time=noon,
            end_time=evening,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift)

        shift = Shift.objects.get_or_create(
            name=SHIFT_NAME_STORAGE_MORNING,
            start_time=morning,
            end_time=noon,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift)

        shift = Shift.objects.get_or_create(
            name=SHIFT_NAME_STORAGE_AFTERNOON,
            start_time=noon,
            end_time=evening,
        )
        for _ in range(3):
            ShiftSlot.objects.create(shift=shift)

    print("Generated test shifts")


def generate_test_user_shifts(user_id):
    user = TapirUser.objects.get(pk=user_id)

    date = timezone.now().today() - datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name=SHIFT_NAME_CASHIER_MORNING, start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.DONE
    )

    date = timezone.now().today() - datetime.timedelta(days=2)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name=SHIFT_NAME_STORAGE_MORNING, start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift,
        user=user,
        state=ShiftAttendance.State.MISSED_EXCUSED,
        excused_reason="Was sick",
    )

    date = timezone.now().today() + datetime.timedelta(days=1)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=8, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name=SHIFT_NAME_CASHIER_MORNING, start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.CANCELLED
    )

    start_time = datetime.datetime.combine(
        date, datetime.time(hour=12, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name=SHIFT_NAME_CASHIER_AFTERNOON, start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.PENDING
    )

    date = timezone.now().today() + datetime.timedelta(days=4)
    start_time = datetime.datetime.combine(
        date, datetime.time(hour=12, tzinfo=datetime.timezone.utc)
    )
    shift = Shift.objects.get(name=SHIFT_NAME_STORAGE_AFTERNOON, start_time=start_time)
    ShiftAttendance.objects.get_or_create(
        shift=shift, user=user, state=ShiftAttendance.State.PENDING
    )

    print("Generated test user " + user.username + "(id=" + str(user_id) + ") shifts")


def generate_test_template_groups():
    ShiftTemplateGroup.objects.all().delete()
    for week in ["A", "B", "C", "D"]:
        ShiftTemplateGroup.objects.get_or_create(name=week)

    print("Generated test template groups")


def get_test_users():
    path_to_json_file = os.path.join(
        pathlib.Path(__file__).parent.absolute(), "test_users.json"
    )
    json_file = open(path_to_json_file, encoding="UTF-8")
    json_string = json_file.read()
    json_file.close()

    return json.loads(json_string)["results"]


USER_COUNT = 400


def generate_test_users():
    # Users generated with https://randomuser.me
    print(f"Creating {USER_COUNT} users, this may take a while")

    parsed_users = get_test_users()
    for index, parsed_user in enumerate(parsed_users[:USER_COUNT]):
        if index % 50 == 0:
            print(str(index) + f"/{USER_COUNT}")
        json_user = JsonUser(parsed_user)
        randomizer = index + 1

        is_company = randomizer % 70 == 0
        is_investing = randomizer % 7 == 0 or is_company

        tapir_user: TapirUser | None = None
        if not is_company and not is_investing:
            tapir_user = TapirUser.objects.create(
                username=json_user.get_username(),
            )
            copy_user_info(json_user, tapir_user)
            tapir_user.is_staff = False
            tapir_user.is_active = True
            tapir_user.date_joined = json_user.date_joined
            tapir_user.password = tapir_user.username
            tapir_user.save()
            tapir_user.set_ldap_password(tapir_user.username)
            if randomizer % 100 == 1:
                ldap_group = LdapGroup.objects.get(cn="vorstand")
                ldap_group.members.append(tapir_user.get_ldap().build_dn())
                ldap_group.save()
            elif randomizer % 25 == 1:
                ldap_group = LdapGroup.objects.get(cn="member-office")
                ldap_group.members.append(tapir_user.get_ldap().build_dn())
                ldap_group.save()

        share_owner = ShareOwner.objects.create(
            is_company=is_company,
            user=tapir_user,
        )
        if tapir_user is None:
            copy_user_info(json_user, share_owner)
        else:
            share_owner.blank_info_fields()

        share_owner.is_investing = randomizer % 7 == 0 or is_company
        share_owner.ratenzahlung = randomizer % 8 == 0
        share_owner.attended_welcome_session = randomizer % 9 != 0
        if share_owner.is_company:
            share_owner.company_name = share_owner.last_name + "'s fancy startup GmbH"
        share_owner.save()

        start_date = json_user.date_joined
        end_date = None
        if randomizer % 40 == 0:
            start_date = json_user.date_joined + datetime.timedelta(weeks=100 * 52)
        elif randomizer % 50 == 0:
            end_date = json_user.date_joined + datetime.timedelta(weeks=100 * 52)
        elif randomizer % 60 == 0:
            end_date = datetime.date(day=18, month=8, year=2020)

        for _ in range(json_user.num_shares):
            ShareOwnership.objects.create(
                share_owner=share_owner,
                start_date=start_date,
                end_date=end_date,
            )

        if (
            not is_company
            and not is_investing
            and not ShiftAttendanceTemplate.objects.filter(user=tapir_user).exists()
        ):
            if random.randint(1, 7) == 1:
                tapir_user.shift_user_data.capabilities.append(
                    ShiftUserCapability.SHIFT_COORDINATOR
                )
                tapir_user.shift_user_data.save()
            if random.randint(1, 4) == 1:
                tapir_user.shift_user_data.capabilities.append(
                    ShiftUserCapability.CASHIER
                )
                tapir_user.shift_user_data.save()
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
    print("Created fake users")


def generate_test_shift_templates():
    if ShiftTemplateGroup.objects.count() < 4:
        generate_test_template_groups()

    slot_name_warenannahme = "Warenannahme & Lager"
    slot_name_cashier = "Kasse"
    slot_name_general = ""
    slot_name_teamleader = "Teamleitung"
    slot_name_cleaning = "Reinigung & Aufräumen"

    start_hours = [(8, 15), (11, 0), (13, 45), (16, 30), (19, 15)]
    first_shift_slots = {
        slot_name_teamleader: 1,
        slot_name_warenannahme: 4,
        slot_name_general: 2,
    }
    last_shift_slots = {
        slot_name_teamleader: 1,
        slot_name_warenannahme: 1,
        slot_name_cleaning: 2,
        slot_name_cashier: 2,
        slot_name_general: 2,
    }
    middle_shift_slots = {
        slot_name_teamleader: 1,
        slot_name_warenannahme: 1,
        slot_name_cashier: 2,
        slot_name_general: 2,
    }
    for weekday in [0, 1, 2, 3, 4, 5]:
        for template_group in ShiftTemplateGroup.objects.all():
            for index, start_hour in enumerate(start_hours):
                start_time = datetime.time(
                    hour=start_hour[0],
                    minute=start_hour[1],
                    tzinfo=timezone.localtime().tzinfo,
                )
                end_time = datetime.time(
                    hour=start_hour[0] + 3,
                    minute=start_hour[1],
                    tzinfo=timezone.localtime().tzinfo,
                )
                shift_template = ShiftTemplate.objects.create(
                    name="Supermarket",
                    group=template_group,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time,
                )

                slots = middle_shift_slots
                if index == 0:
                    slots = first_shift_slots
                if index == len(start_hours) - 1:
                    slots = last_shift_slots

                for slot_name, slot_quantity in slots.items():
                    capabilities = []
                    if slot_name == "Teamleitung":
                        capabilities = [ShiftUserCapability.SHIFT_COORDINATOR]
                    if slot_name == "Kasse":
                        capabilities = [ShiftUserCapability.CASHIER]
                    for index in range(slot_quantity):
                        ShiftSlotTemplate.objects.create(
                            name=slot_name,
                            shift_template=shift_template,
                            required_capabilities=capabilities,
                        )

    print("Generated test shift templates")


def generate_shifts(print_progress=False):
    if print_progress:
        print("Generating shifts")
    start_day = get_monday(timezone.now().today() - datetime.timedelta(days=20))

    groups = ShiftTemplateGroup.objects.all()
    for week in range(8):
        monday = start_day + datetime.timedelta(days=7 * week)
        if print_progress:
            print("Doing week from " + str(monday) + " " + str(week + 1) + "/8")
        groups[week % 4].create_shifts(monday)
    if print_progress:
        print("Generated shifts")


def generate_test_applicants():
    parsed_users = get_test_users()
    for index, parsed_user in enumerate(parsed_users[USER_COUNT : USER_COUNT + 50]):
        json_user = JsonUser(parsed_user)
        randomizer = index + 1
        draft_user = DraftUser.objects.create()
        copy_user_info(json_user, draft_user)

        if randomizer % 3 == 0:
            draft_user.attended_welcome_session = True
        if randomizer % 4 == 0:
            draft_user.signed_membership_agreement = True
        if randomizer % 5 == 0:
            draft_user.paid_membership_fee = True

        draft_user.save()


def clear_data():
    print("Clearing data...")
    classes = [
        LogEntry,
        ShiftAttendance,
        ShiftCycleEntry,
        ShiftAccountEntry,
        Shift,
        ShiftAttendanceTemplate,
        ShiftTemplate,
        ShiftTemplateGroup,
        ShiftUserData,
        ShareOwnership,
        IncomingPayment,
        NewMembershipsForAccountingRecap,
        ExtraSharesForAccountingRecap,
        ShareOwner,
        DraftUser,
        ProcessedPurchaseFiles,
        PurchaseBasket,
    ]
    for cls in classes:
        cls.objects.all().delete()
    TapirUser.objects.filter(is_staff=False).delete()
    print("Done")


def generate_purchase_baskets():
    current_date = ShareOwnership.objects.order_by("start_date").first().start_date
    # starting not too long ago to avoid taking too much time
    current_date: datetime.date = max(
        current_date, datetime.date(year=2023, month=1, day=1)
    )
    today = timezone.now().date()
    current_month = -1
    while current_date < today:
        if current_date.month != current_month:
            current_month = current_date.month
            print(
                f"Generating purchase baskets for {current_date.strftime('%d.%m.%Y')}"
            )

        source_file = ProcessedPurchaseFiles.objects.create(
            file_name=f"test_basket_file{current_date.strftime('%d.%m.%Y')}",
            processed_on=get_timezone_aware_datetime(
                current_date, datetime.time(hour=random.randint(0, 23))
            ),
        )

        purchasing_users = [
            share_owner
            for share_owner in ShareOwner.objects.with_status(
                status=MemberStatus.ACTIVE, date=current_date
            )
            if share_owner.user
        ]
        baskets = [
            PurchaseBasket(
                source_file=source_file,
                purchase_date=get_timezone_aware_datetime(
                    current_date - datetime.timedelta(days=random.randint(0, 6)),
                    datetime.time(hour=random.randint(0, 23)),
                ),
                cashier=random.randint(0, 10),
                purchase_counter=random.randint(0, 10),
                tapir_user=share_owner.user,
                gross_amount=random.randrange(1, 100),
                first_net_amount=0,
                second_net_amount=0,
                discount=0,
            )
            for share_owner in purchasing_users
        ]
        PurchaseBasket.objects.bulk_create(baskets)

        current_date += datetime.timedelta(days=7)


def reset_all_test_data():
    random.seed("supercoop")
    clear_data()
    generate_test_template_groups()
    generate_test_shift_templates()
    generate_shifts(True)
    generate_test_users()
    generate_test_applicants()
    generate_purchase_baskets()

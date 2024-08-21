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
from tapir.coop.services.MemberInfoService import MemberInfoService
from tapir.coop.services.MembershipPauseService import MembershipPauseService
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

USER_COUNT = 400


def generate_test_template_groups():
    ShiftTemplateGroup.objects.all().delete()
    ShiftTemplateGroup.objects.bulk_create(
        [ShiftTemplateGroup(name=week) for week in ["A", "B", "C", "D"]]
    )
    print("Generated test template groups")


def get_test_users():
    path_to_json_file = os.path.join(
        pathlib.Path(__file__).parent.absolute(), "test_users.json"
    )
    json_file = open(path_to_json_file, encoding="UTF-8")
    json_string = json_file.read()
    json_file.close()
    parsed_users = json.loads(json_string)["results"]
    return [JsonUser(parsed_user) for parsed_user in parsed_users[:USER_COUNT]]


def determine_is_company(randomizer: int) -> bool:
    return randomizer % 70 == 0


def determine_is_investing(randomizer: int, is_company: bool) -> bool:
    return randomizer % 7 == 0 or is_company


def generate_tapir_users(json_users):
    result = []
    for index, json_user in enumerate(json_users):
        randomizer = index + 1

        is_company = determine_is_company(randomizer)
        is_investing = determine_is_investing(randomizer, is_company)

        if is_company or is_investing:
            result.append(None)
            continue

        tapir_user = TapirUser(
            username=json_user.get_username(),
        )
        copy_user_info(json_user, tapir_user)
        tapir_user.is_staff = False
        tapir_user.is_active = True
        tapir_user.date_joined = json_user.date_joined
        tapir_user.password = tapir_user.username
        result.append(tapir_user)

    tapir_users = [tapir_user for tapir_user in result if tapir_user is not None]
    TapirUser.objects.bulk_create(tapir_users)

    for tapir_user in tapir_users:
        tapir_user.set_ldap_password(tapir_user.username)

    vorstand_users = []
    member_office_users = []
    for index, tapir_user in enumerate(result):
        if tapir_user is None:
            continue

        randomizer = index + 1

        if randomizer % 100 == 1:
            vorstand_users.append(tapir_user)
        elif randomizer % 25 == 1:
            member_office_users.append(tapir_user)

    vorstand_ldap_group = LdapGroup.objects.get(cn="vorstand")
    vorstand_ldap_group.members.extend(
        [tapir_user.get_ldap().build_dn() for tapir_user in vorstand_users]
    )
    vorstand_ldap_group.save()

    member_office_ldap_group = LdapGroup.objects.get(cn="member-office")
    member_office_ldap_group.members.extend(
        [tapir_user.get_ldap().build_dn() for tapir_user in member_office_users]
    )
    member_office_ldap_group.save()

    return result


def generate_share_owners(json_users, tapir_users):
    share_owners = []
    for index, json_user in enumerate(json_users):
        randomizer = index + 1

        is_company = determine_is_company(randomizer)
        is_investing = determine_is_investing(randomizer, is_company)

        tapir_user = tapir_users[index]
        share_owner = ShareOwner(
            is_company=is_company,
            user=tapir_user,
        )

        if tapir_user is None:
            copy_user_info(json_user, share_owner)
        else:
            share_owner.blank_info_fields()

        share_owner.is_investing = is_investing
        share_owner.ratenzahlung = randomizer % 8 == 0
        share_owner.attended_welcome_session = randomizer % 9 != 0
        if share_owner.is_company:
            share_owner.company_name = share_owner.last_name + "'s fancy startup GmbH"
        share_owners.append(share_owner)

    ShareOwner.objects.bulk_create(share_owners)

    return share_owners


def generate_share_ownerships(json_users, share_owners):
    share_ownerships = []
    for index, json_user in enumerate(json_users):
        randomizer = index + 1
        share_owner = share_owners[index]

        start_date = json_user.date_joined
        end_date = None
        if randomizer % 40 == 0:
            start_date = json_user.date_joined + datetime.timedelta(weeks=100 * 52)
        elif randomizer % 50 == 0:
            end_date = json_user.date_joined + datetime.timedelta(weeks=100 * 52)
        elif randomizer % 60 == 0:
            end_date = datetime.date(day=18, month=8, year=2020)

        for _ in range(json_user.num_shares):
            share_ownerships.append(
                ShareOwnership(
                    share_owner=share_owner,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

    return ShareOwnership.objects.bulk_create(share_ownerships)


def generate_shift_user_datas(tapir_users):
    shift_user_datas = [
        ShiftUserData(user=tapir_user)
        for tapir_user in tapir_users
        if tapir_user is not None
    ]

    for shift_user_data in shift_user_datas:
        if random.randint(1, 7) == 1:
            shift_user_data.capabilities.append(ShiftUserCapability.SHIFT_COORDINATOR)
        if random.randint(1, 4) == 1:
            shift_user_data.capabilities.append(ShiftUserCapability.CASHIER)

    return ShiftUserData.objects.bulk_create(shift_user_datas)


def generate_test_users():
    # Users generated with https://randomuser.me
    print(f"Creating {USER_COUNT} users, this may take a while")

    json_users = get_test_users()
    print("\tCreating tapir_users")
    tapir_users = generate_tapir_users(json_users)
    print("\tCreating share_owners")
    share_owners = generate_share_owners(json_users, tapir_users)
    print("\tCreating share_ownerships")
    generate_share_ownerships(json_users, share_owners)
    print("\tCreating shift_user_datas")
    generate_shift_user_datas(tapir_users)

    print("\tRegistering users to shifts")
    shift_templates = list(
        ShiftTemplate.objects.all().prefetch_related(
            "slot_templates__attendance_template"
        )
    )
    for index, parsed_user in enumerate(json_users):
        randomizer = index + 1

        is_company = determine_is_company(randomizer)
        is_investing = determine_is_investing(randomizer, is_company)
        if is_company or is_investing:
            continue

        tapir_user = tapir_users[index]

        random_templates = random.choices(shift_templates, k=10)
        for shift_template in random_templates:
            attendance_template_created = False

            for free_slot in shift_template.slot_templates.all():
                # Attend the first one fit for this user.
                if not free_slot.user_can_attend(tapir_user):
                    continue
                ShiftAttendanceTemplate.objects.create(
                    user=tapir_user, slot_template=free_slot
                )
                free_slot.update_future_slot_attendances()
                attendance_template_created = True
                break

            if attendance_template_created:
                break
    print("Created fake users")


def generate_test_shift_templates():
    if ShiftTemplateGroup.objects.count() < 4:
        generate_test_template_groups()

    slot_name_warenannahme = "Warenannahme & Lagerhaltung"
    slot_name_cashier = "Kasse"
    slot_name_general = "Allgemein"
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
    template_groups = ShiftTemplateGroup.objects.all()
    shift_templates = []

    for weekday in [0, 1, 2, 3, 4, 5]:
        for template_group in template_groups:
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
                shift_templates.append(
                    ShiftTemplate(
                        name="Supermarket",
                        group=template_group,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=end_time,
                    )
                )

    shift_templates = ShiftTemplate.objects.bulk_create(shift_templates)

    slot_templates = []
    for shift_template in shift_templates:
        slots = middle_shift_slots
        if shift_template.start_time.hour == start_hours[0][0]:
            slots = first_shift_slots
        if shift_template.start_time.hour == start_hours[-1][0]:
            slots = last_shift_slots

        for slot_name, slot_quantity in slots.items():
            capabilities = []
            if slot_name == "Teamleitung":
                capabilities = [ShiftUserCapability.SHIFT_COORDINATOR]
            if slot_name == "Kasse":
                capabilities = [ShiftUserCapability.CASHIER]
            for _ in range(slot_quantity):
                slot_templates.append(
                    ShiftSlotTemplate(
                        name=slot_name,
                        shift_template=shift_template,
                        required_capabilities=capabilities,
                    )
                )
    ShiftSlotTemplate.objects.bulk_create(slot_templates)

    print("Generated test shift templates")


def generate_shifts():
    print("Generating shifts")
    start_day = get_monday(timezone.now().date() - datetime.timedelta(days=20))

    groups = ShiftTemplateGroup.objects.all()
    groups = {index: group for index, group in enumerate(groups)}
    for week in range(8):
        monday = start_day + datetime.timedelta(days=7 * week)
        groups[week % 4].create_shifts(monday)


def generate_test_applicants():
    parsed_users = get_test_users()
    draft_users = []
    for index, parsed_user in enumerate(parsed_users[USER_COUNT : USER_COUNT + 50]):
        json_user = JsonUser(parsed_user)
        randomizer = index + 1
        draft_user = DraftUser()
        copy_user_info(json_user, draft_user)

        if randomizer % 3 == 0:
            draft_user.attended_welcome_session = True
        if randomizer % 4 == 0:
            draft_user.signed_membership_agreement = True
        if randomizer % 5 == 0:
            draft_user.paid_membership_fee = True

        draft_users.append(draft_user)

    DraftUser.objects.bulk_create(draft_users)


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
    print("Generating purchase baskets")
    current_date = ShareOwnership.objects.order_by("start_date").first().start_date
    # starting not too long ago to avoid taking too much time
    current_date: datetime.date = max(
        current_date, datetime.date(year=2023, month=1, day=1)
    )
    today = timezone.now().date()

    weeks = []

    while current_date < today:
        weeks.append(current_date)
        current_date += datetime.timedelta(days=7)

    processed_purchase_files = [
        ProcessedPurchaseFiles(
            file_name=f"test_basket_file{current_date.strftime('%d.%m.%Y')}",
            processed_on=get_timezone_aware_datetime(
                week, datetime.time(hour=random.randint(0, 23))
            ),
        )
        for week in weeks
    ]
    files: list[ProcessedPurchaseFiles] = ProcessedPurchaseFiles.objects.bulk_create(
        processed_purchase_files
    )

    baskets = []
    for file in files:
        current_date = file.processed_on
        share_owners = ShareOwner.objects.prefetch_related("user")
        share_owners = (
            MemberInfoService.annotate_share_owner_queryset_with_nb_of_active_shares(
                share_owners, current_date
            )
        )
        share_owners = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, current_date
            )
        )

        purchasing_users = [
            share_owner
            for share_owner in share_owners.with_status(
                status=MemberStatus.ACTIVE, date=current_date
            )
            if share_owner.user
        ]
        baskets.extend(
            [
                PurchaseBasket(
                    source_file=file,
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
        )

    PurchaseBasket.objects.bulk_create(baskets)
    print("Done")


def reset_all_test_data():
    random.seed("supercoop")
    clear_data()
    generate_test_template_groups()
    generate_test_shift_templates()
    generate_shifts()
    generate_test_users()
    generate_test_applicants()
    generate_purchase_baskets()

import datetime
import json
import os
import pathlib
import random

import ldap
from django.utils import timezone
from django_auth_ldap.config import LDAPSearch
from fabric.testing.fixtures import connection
from faker import Faker
from ldap.ldapobject import LDAPObject

from tapir import settings
from tapir.accounts.models import TapirUser, UpdateTapirUserLogEntry
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.models import (
    ShareOwner,
    ShareOwnership,
    DraftUser,
    IncomingPayment,
    NewMembershipsForAccountingRecap,
    ExtraSharesForAccountingRecap,
    MemberStatus,
    MembershipResignation,
)
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.log.models import LogEntry
from tapir.settings import GROUP_VORSTAND, GROUP_MEMBER_OFFICE
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
    ShiftAttendanceMode,
    CreateShiftAttendanceTemplateLogEntry,
)
from tapir.statistics.models import (
    ProcessedPurchaseFiles,
    PurchaseBasket,
    ProcessedCreditFiles,
    CreditAccount,
    FancyGraphCache,
)
from tapir.utils.json_user import JsonUser
from tapir.utils.models import copy_user_info
from tapir.utils.shortcuts import (
    get_monday,
    get_timezone_aware_datetime,
    set_group_membership,
    get_admin_ldap_connection,
    build_ldap_group_dn,
)

SHIFT_NAME_CASHIER_MORNING = "Cashier morning"
SHIFT_NAME_CASHIER_AFTERNOON = "Cashier afternoon"
SHIFT_NAME_STORAGE_MORNING = "Storage morning"
SHIFT_NAME_STORAGE_AFTERNOON = "Storage afternoon"

USER_COUNT = 400
DRAFT_USER_COUNT = 50


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
    return [
        JsonUser(parsed_user)
        for parsed_user in parsed_users[: USER_COUNT + DRAFT_USER_COUNT]
    ]


def determine_is_company(randomizer: int) -> bool:
    return randomizer % 70 == 0


def determine_is_investing(randomizer: int, is_company: bool) -> bool:
    return randomizer % 7 == 0 or is_company


def determine_is_abcd(randomizer: int) -> bool:
    return randomizer % 4 == 0


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
        tapir_user.co_purchaser = Faker().name() if random.random() > 0.5 else ""
        result.append(tapir_user)

    tapir_users = [tapir_user for tapir_user in result if tapir_user is not None]
    tapir_users = TapirUser.objects.bulk_create(tapir_users)
    for tapir_user in tapir_users:
        tapir_user.create_ldap()

    for tapir_user in tapir_users:
        tapir_user.set_password(tapir_user.username)

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

    set_group_membership(vorstand_users, GROUP_VORSTAND, True)
    set_group_membership(member_office_users, GROUP_MEMBER_OFFICE, True)

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
        if random.randint(1, 2) == 1:
            shift_user_data.attendance_mode = ShiftAttendanceMode.REGULAR
        else:
            shift_user_data.attendance_mode = ShiftAttendanceMode.FLYING
        if random.randint(1, 7) == 1:
            shift_user_data.capabilities.append(ShiftUserCapability.SHIFT_COORDINATOR)
        if random.randint(1, 4) == 1:
            shift_user_data.capabilities.append(ShiftUserCapability.CASHIER)

    return ShiftUserData.objects.bulk_create(shift_user_datas)


def generate_test_users():
    # Users generated with https://randomuser.me
    print(f"Creating {USER_COUNT} users, this may take a while")

    json_users = get_test_users()[:USER_COUNT]
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
        is_abcd = determine_is_abcd(randomizer)
        if is_company or is_investing or not is_abcd:
            continue

        tapir_user = tapir_users[index]

        random_templates = random.choices(shift_templates, k=10)
        log_entries = []
        for shift_template in random_templates:
            attendance_template_created = False

            for free_slot in shift_template.slot_templates.all():
                # Attend the first one fit for this user.
                if not free_slot.user_can_attend(tapir_user):
                    continue
                attendance_template = ShiftAttendanceTemplate.objects.create(
                    user=tapir_user, slot_template=free_slot
                )
                log_entry = CreateShiftAttendanceTemplateLogEntry().populate(
                    actor=None,
                    tapir_user=tapir_user,
                    shift_attendance_template=attendance_template,
                )
                log_entry.save()
                log_entries.append(log_entry)
                free_slot.update_future_slot_attendances(SHIFT_GENERATION_START)
                attendance_template_created = True
                break

            if attendance_template_created:
                break

        for log_entry in log_entries:
            log_entry.created_date = log_entry.user.date_joined + datetime.timedelta(
                weeks=random.randint(1, 100)
            )
            log_entry.created_date = min(timezone.now(), log_entry.created_date)
        CreateShiftAttendanceTemplateLogEntry.objects.bulk_update(
            log_entries, ["created_date"]
        )

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


SHIFT_GENERATION_START = timezone.now().date() - datetime.timedelta(days=100)


def generate_shifts():
    print("Generating shifts")
    start_day = get_monday(SHIFT_GENERATION_START)

    groups = ShiftTemplateGroup.objects.all()
    groups = {index: group for index, group in enumerate(groups)}
    for week in range(20):
        monday = start_day + datetime.timedelta(days=7 * week)
        groups[week % 4].create_shifts(monday)


def generate_test_applicants():
    json_users = get_test_users()
    draft_users = []
    for index, json_user in enumerate(json_users[USER_COUNT : USER_COUNT + 50]):
        randomizer = index + 1
        draft_user = DraftUser()
        copy_user_info(json_user, draft_user)

        if randomizer % 3 == 0:
            draft_user.attended_welcome_session = True
        if randomizer % 4 == 0:
            draft_user.signed_membership_agreement = True

        draft_users.append(draft_user)

    DraftUser.objects.bulk_create(draft_users)


def remove_users_from_group(connection: LDAPObject, group_name: str, tapir_users):
    connection.modify_s(
        build_ldap_group_dn(group_name),
        [
            (
                ldap.MOD_DELETE,
                "member",
                [
                    tapir_user.build_ldap_dn().encode("utf-8")
                    for tapir_user in tapir_users
                ],
            )
        ],
    )


def clear_ldap():
    tapir_users = TapirUser.objects.all()
    connection = get_admin_ldap_connection()
    for group_name in settings.LDAP_GROUPS:
        search = LDAPSearch(
            "ou=groups,dc=supercoop,dc=de", ldap.SCOPE_SUBTREE, f"(cn={group_name})"
        )
        result = search.execute(connection)
        if result:
            connection.delete_s(build_ldap_group_dn(group_name))

    search = LDAPSearch("ou=people,dc=supercoop,dc=de", ldap.SCOPE_SUBTREE)
    search_results = search.execute(connection)
    for search_result in search_results:
        user_dn = search_result[0]
        if not user_dn.startswith("uid="):
            continue
        connection.delete_s(user_dn)


def clear_django_db():
    classes = [
        LogEntry,
        MembershipResignation,
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
        FancyGraphCache,
    ]
    ShareOwnership.objects.update(transferred_from=None)
    for cls in classes:
        cls.objects.all().delete()
    TapirUser.objects.filter(is_staff=False).delete()


def clear_data():
    print("Clearing data...")

    clear_ldap()
    clear_django_db()

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
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            share_owners, current_date
        )
        share_owners = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, current_date
            )
        )

        purchasing_users = [
            share_owner
            for share_owner in share_owners.with_status(
                status=MemberStatus.ACTIVE, at_datetime=current_date
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


def generate_credit_account():
    print("Generating credit account")
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

    processed_credit_files = [
        ProcessedCreditFiles(
            file_name=f"test_credit_file{current_date.strftime('%d.%m.%Y')}",
            processed_on=get_timezone_aware_datetime(
                week, datetime.time(hour=random.randint(0, 23))
            ),
        )
        for week in weeks
    ]
    files: list[ProcessedCreditFiles] = ProcessedCreditFiles.objects.bulk_create(
        processed_credit_files
    )

    account_credits = []
    for file in files:
        current_date = file.processed_on
        share_owners = ShareOwner.objects.prefetch_related("user")
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            share_owners, current_date
        )
        credit_users = [
            share_owner
            for share_owner in share_owners.with_status(
                status=MemberStatus.ACTIVE, at_datetime=current_date
            )[::2]
            if share_owner.user
        ]
        info = random.choice(["Guthabenkarte", "Einkauf"])
        credit_amount = (
            random.randrange(0, 100)
            if info == "Guthabenkarte"
            else random.randrange(-100, 0)
        )
        account_credits.extend(
            [
                CreditAccount(
                    source_file=file,
                    credit_date=get_timezone_aware_datetime(
                        current_date - datetime.timedelta(days=random.randint(0, 6)),
                        datetime.time(hour=random.randint(0, 23)),
                    ),
                    credit_amount=credit_amount,
                    credit_counter=random.randint(0, 10),
                    cashier=random.randint(0, 10),
                    info=info,
                    tapir_user=share_owner.user,
                )
                for share_owner in credit_users
            ]
        )

    CreditAccount.objects.bulk_create(account_credits)


def generate_log_updates():
    print("Generating history of changes")
    tapir_users = [tapir_user for tapir_user in TapirUser.objects.all()]
    logs = {}
    now = timezone.now()
    fields = UserDataFactory.ATTRIBUTES + ["co_purchaser"]

    nb_logs_to_create = TapirUser.objects.count() * 2
    for _ in range(nb_logs_to_create):
        tapir_user = random.choice(tapir_users)
        if (now - tapir_user.date_joined).days < 7:
            continue

        if tapir_user in logs.keys():
            oldest_log = logs[tapir_user][-1]
            reference_date = oldest_log.created_date
        else:
            reference_date = now

        date_range = round((reference_date - tapir_user.date_joined).days / 2.0)
        le_random = random.randint(1, date_range)
        log_date = now - datetime.timedelta(days=le_random)

        log = UpdateTapirUserLogEntry(
            created_date=log_date, user=tapir_user, actor=random.choice(tapir_users)
        )
        if tapir_user not in logs.keys():
            logs[tapir_user] = []

        old_values_reference = TapirUserFactory.build()
        nb_fields = random.randint(1, 5)
        fields_in_log = set()
        for _ in range(nb_fields):
            fields_in_log.add(random.choice(fields))

        log.old_values = {}
        log.new_values = {}
        for field in fields_in_log:
            old_value = getattr(old_values_reference, field)

            new_value = None
            for newer_log in logs[tapir_user]:
                if field in newer_log.new_values.keys():
                    new_value = newer_log.new_values.get(field)
                    break
            if new_value is None:
                new_value = getattr(tapir_user, field)
            if old_value != new_value:
                log.old_values[field] = old_value
                log.new_values[field] = new_value

        log.save()
        # the date gets overriden on creating since the field has auto_now_add
        log.created_date = log_date
        log.save()
        logs[tapir_user].append(log)


def update_attendances():
    print("Updating attendances")
    attendances = [
        attendance
        for attendance in ShiftAttendance.objects.filter(
            slot__shift__start_time__lte=timezone.now()
        )
    ]
    for attendance in attendances:
        attendance.state = random.choice(ShiftAttendance.State.choices)[0]
    ShiftAttendance.objects.bulk_update(attendances, ["state"])
    attendances = ShiftAttendance.objects.all().prefetch_related("account_entry")
    for attendance in attendances:
        attendance.update_shift_account_entry()


def reset_all_test_data():
    random.seed("supercoop")
    clear_data()
    generate_test_template_groups()
    generate_test_shift_templates()
    generate_shifts()
    generate_test_users()
    generate_test_applicants()
    generate_purchase_baskets()
    generate_credit_account()
    generate_log_updates()
    update_attendances()

    print("Done")

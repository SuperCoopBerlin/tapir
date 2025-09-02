import datetime

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.exceptions import CoopsPtRequestException
from tapir.rizoma.models import RizomaMemberData
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator
from tapir.shifts.models import ShiftUserData
from tapir.utils.models import copy_user_info


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            help="Deletes all ShareOwners and TapirUsers before syncing",
            action="store_true",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["reset"]:
                ShareOwner.objects.all().delete()
                TapirUser.objects.all().delete()

            self.sync_members()
            external_member_id_to_user_id_map = self.sync_users()
            self.sync_link_share_owner_to_user(external_member_id_to_user_id_map)
            self.create_users_for_all_members()

    @classmethod
    def sync_users(cls):
        response = CoopsPtRequestHandler.get("users?_search=")
        if response.status_code != 200:
            raise CoopsPtRequestException("Failed to get user list from coops.pt")

        # Example element from the response.data list:
        # {'_created_at': '2025-06-20T12:52:36.373Z',
        #    '_deleted_at': None,
        #    '_id': 'fc40605e-1376-4554-8b29-7041eddf6660',
        #    '_memberName': None,
        #    '_updated_at': '2025-06-20T12:52:36.373Z',
        #    'email': 'ilamosciski@fadel.org',
        #    'firstName': 'Charlotte',
        #    'lastName': 'Denesik',
        #    'memberId': None,
        #    'recover_string': None,
        #    'suspended': False,
        #    'type': 'member'},

        response_content = response.json()
        users_to_create = []
        users_to_update = set()
        tapir_users_by_external_id = {
            tapir_user.external_id: tapir_user for tapir_user in TapirUser.objects.all()
        }
        external_ids_present_in_coops_pt = set()
        external_member_id_to_user_id_map = {}
        for user_json in response_content["data"]:
            if user_json.get("_deleted_at", None) is not None:
                continue
            external_user_id = user_json["_id"]
            external_ids_present_in_coops_pt.add(external_user_id)

            user = tapir_users_by_external_id.get(external_user_id, None)
            if user is not None:
                user = tapir_users_by_external_id[external_user_id]
                if user.first_name != user_json["firstName"]:
                    user.first_name = user_json["firstName"]
                    users_to_update.add(user)
                if user.last_name != user_json["lastName"]:
                    user.last_name = user_json["lastName"]
                    users_to_update.add(user)
                if CoopsPtAuthBackend.update_admin_status(user, user_json["type"]):
                    users_to_update.add(user)
            else:
                users_to_create.append(
                    CoopsPtUserCreator.build_tapir_user_from_api_response(user_json)
                )

            external_member_id = user_json["memberId"]
            if external_member_id is not None:
                external_member_id_to_user_id_map[external_member_id] = external_user_id

        users = TapirUser.objects.bulk_create(users_to_create)
        ShiftUserData.objects.bulk_create([ShiftUserData(user=user) for user in users])
        TapirUser.objects.bulk_update(
            users_to_update, ["first_name", "last_name", "is_superuser"]
        )

        emails_to_delete = set(tapir_users_by_external_id.keys()).difference(
            external_ids_present_in_coops_pt
        )
        TapirUser.objects.filter(email__in=emails_to_delete).delete()

        return external_member_id_to_user_id_map

    @classmethod
    def sync_members(cls):
        response = CoopsPtRequestHandler.get("members?_search=")
        if response.status_code != 200:
            raise CoopsPtRequestException("Failed to get user list from coops.pt")

        response_content = response.json()
        share_owners_to_create = []
        external_ids_present_in_tapir_db = set(
            ShareOwner.objects.values_list("external_id", flat=True)
        )
        external_ids_present_in_coops_pt = set()
        used_member_numbers = set()
        member_number_to_photo_id_map = {}

        # Example element from the response:
        # {'_created_at': '2025-08-08T14:12:54.323Z',
        #                        '_currentState': 'Consumo, Cultura',
        #                        '_currentStateDate': '2023-10-23T00:00:00Z',
        #                        '_deleted_at': None,
        #                        '_firstEmail': 'example@example.com',
        #                        '_firstMobile': '017625321321',
        #                        '_fullAddress': 'Test address',
        #                        '_id': 'SOME_UUID',
        #                        '_isActiveSince': '2023-10-23T00:00:00Z',
        #                        '_photoId': 'SOME_UUID',
        #                        '_updated_at': '2025-09-02T12:16:59.09Z',
        #                        'address': 'Test post address',
        #                        'birthday': '1993-09-24T00:00:00Z',
        #                        'city': 'Lisboa',
        #                        'countryId': 1,
        #                        'fiscalNumber': '123456789',
        #                        'idCardNumber': '12345678',
        #                        'name': 'John Doe',
        #                        'nationalityId': None,
        #                        'notes': '',
        #                        'number': 720,
        #                        'zip': '1600-668'

        for share_owner_json in response_content["data"]:
            if (
                share_owner_json["_deleted_at"] is not None
                or share_owner_json["_firstEmail"] is None
            ):
                continue

            member_number = share_owner_json["number"]
            if settings.DEBUG:
                # on the demo instance demo.coopts.pt, several members have the same number.
                # This is invalid, but it should not happen with production instances
                if member_number in used_member_numbers:
                    continue
                used_member_numbers.add(member_number)

            external_id = share_owner_json["_id"]
            external_ids_present_in_coops_pt.add(external_id)
            if external_id in external_ids_present_in_tapir_db:
                continue

            name: str = share_owner_json["name"]
            name_parts = name.split(maxsplit=1)
            first_name = None
            if len(name_parts) > 0:
                first_name = name_parts[0]
            last_name = None
            if len(name_parts) > 1:
                last_name = name_parts[1]
            birthday = None
            if share_owner_json["birthday"] is not None:
                birthday = datetime.datetime.fromisoformat(share_owner_json["birthday"])

            share_owners_to_create.append(
                ShareOwner(
                    id=member_number,
                    external_id=external_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=share_owner_json["_firstEmail"],
                    birthdate=birthday,
                    street=share_owner_json["address"],
                    postcode=share_owner_json["zip"],
                    city=share_owner_json["city"][:50],
                    preferred_language="pt",
                )
            )
            member_number_to_photo_id_map[member_number] = share_owner_json.get(
                "_photoId", None
            )

        share_owners = ShareOwner.objects.bulk_create(share_owners_to_create)
        RizomaMemberData.objects.bulk_create(
            [
                RizomaMemberData(
                    share_owner=share_owner,
                    photo_id=member_number_to_photo_id_map[share_owner.id],
                )
                for share_owner in share_owners
            ]
        )

        external_ids_to_delete = external_ids_present_in_tapir_db.difference(
            external_ids_present_in_coops_pt
        )
        ShareOwner.objects.filter(id__in=external_ids_to_delete).delete()

    @classmethod
    def sync_link_share_owner_to_user(cls, external_member_id_to_user_id_map):
        tapir_users_by_external_id = {
            tapir_user.external_id: tapir_user for tapir_user in TapirUser.objects.all()
        }
        share_owners_by_external_id = {
            share_owner.external_id: share_owner
            for share_owner in ShareOwner.objects.all()
        }

        share_owners_to_update = []
        tapir_user_ids_to_delete = []
        for share_owner in share_owners_by_external_id.values():
            linked_tapir_user_id = None
            if share_owner.external_id in external_member_id_to_user_id_map.keys():
                linked_tapir_user = tapir_users_by_external_id.get(
                    external_member_id_to_user_id_map[share_owner.external_id], None
                )
                linked_tapir_user_id = (
                    linked_tapir_user.id if linked_tapir_user is not None else None
                )

            if (
                linked_tapir_user_id is not None
                and linked_tapir_user_id != share_owner.user_id
            ):
                if share_owner.user_id is not None:
                    tapir_user_ids_to_delete.append(share_owner.user_id)

                share_owner.user_id = linked_tapir_user_id
                share_owners_to_update.append(share_owner)

        ShareOwner.objects.bulk_update(share_owners_to_update, ["user_id"])
        TapirUser.objects.filter(id__in=tapir_user_ids_to_delete).delete()

    @classmethod
    def create_users_for_all_members(cls):
        # Currently, most members in the coops.pt data are not linked to any user.
        # They are however still registered to shifts.
        # So, in order to represent the registrations, we create "fake" tapir users that can't be used to login.
        existing_tapir_users_emails = set(
            TapirUser.objects.values_list("email", flat=True)
        )
        tapir_users_to_create = []
        share_owners: list[ShareOwner] = list(
            ShareOwner.objects.filter(user__isnull=True)
        )
        existing_share_owner_mails = list(
            ShareOwner.objects.values_list("email", flat=True)
        )
        duplicate_mails = set(
            [
                mail
                for mail in existing_share_owner_mails
                if existing_share_owner_mails.count(mail) > 1
            ]
        )

        for share_owner in share_owners:
            tapir_user = TapirUser(is_active=False, username=share_owner.email)
            copy_user_info(source=share_owner, target=tapir_user)
            if (
                tapir_user.email in duplicate_mails
                or share_owner.email in existing_tapir_users_emails
            ):
                prefix, suffix = tapir_user.email.split("@", 1)
                prefix = f"{prefix}+rizoma_{share_owner.id}"
                tapir_user.email = f"{prefix}@{suffix}"
                tapir_user.username = tapir_user.email
            tapir_users_to_create.append(tapir_user)

        tapir_users = TapirUser.objects.bulk_create(tapir_users_to_create)
        ShiftUserData.objects.bulk_create(
            [ShiftUserData(user=user) for user in tapir_users]
        )

        for index, share_owner in enumerate(share_owners):
            share_owner.user_id = tapir_users[index].id
        ShareOwner.objects.bulk_update(share_owners, ["user_id"])

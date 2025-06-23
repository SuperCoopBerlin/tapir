import requests
from django.conf import settings
from django.core.management import BaseCommand

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.rizoma.coops_pt_auth_backend import CoopsPtAuthBackend
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator
from tapir.utils.expection_utils import TapirException


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.post(
            url=f"{settings.COOPS_PT_API_BASE_URL}/auth",
            headers={"Accept": "application/json"},
            data=f'{{"email": "{settings.COOPS_PT_ADMIN_EMAIL}", "password": "{settings.COOPS_PT_ADMIN_PASSWORD}"}}',
        )
        if response.status_code != 200:
            raise TapirException(
                "Failed to login to coops.pt with admin credentials from settings"
            )

        response_content = response.json()
        access_token = response_content.get("access", None)

        self.sync_members(access_token)
        external_member_id_to_user_id_map = self.sync_users(access_token)
        self.sync_link_share_owner_to_user(external_member_id_to_user_id_map)

    @classmethod
    def sync_users(cls, access_token):
        response = requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/users?_search=",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            raise TapirException("Failed to get user list from coops.pt")

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

        len(TapirUser.objects.bulk_create(users_to_create))
        TapirUser.objects.bulk_update(
            users_to_update, ["first_name", "last_name", "is_superuser"]
        )

        emails_to_delete = set(tapir_users_by_external_id.keys()).difference(
            external_ids_present_in_coops_pt
        )
        TapirUser.objects.filter(email__in=emails_to_delete).delete()

        return external_member_id_to_user_id_map

    @classmethod
    def sync_members(cls, access_token):
        response = requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/members?_search=",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            raise TapirException("Failed to get user list from coops.pt")

        response_content = response.json()
        share_owners_to_create = []
        external_ids_present_in_tapir_db = set(
            ShareOwner.objects.values_list("external_id", flat=True)
        )
        external_ids_present_in_coops_pt = set()
        used_member_numbers = set()

        for share_owner_json in response_content["data"]:
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
            share_owners_to_create.append(
                ShareOwner(id=member_number, external_id=external_id)
            )

        len(ShareOwner.objects.bulk_create(share_owners_to_create))

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
        for share_owner in share_owners_by_external_id.values():
            linked_tapir_user_id = None
            if share_owner.external_id in external_member_id_to_user_id_map.keys():
                linked_tapir_user = tapir_users_by_external_id.get(
                    external_member_id_to_user_id_map[share_owner.external_id], None
                )
                linked_tapir_user_id = (
                    linked_tapir_user.id if linked_tapir_user is not None else None
                )

            if linked_tapir_user_id != share_owner.user_id:
                share_owner.user_id = linked_tapir_user_id
                share_owners_to_update.append(share_owner)

        ShareOwner.objects.bulk_update(share_owners_to_update, ["user_id"])

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
    # If your coops.pt data gets reset, you may get the same members and accounts,
    # with the same member number and email addresses respectively, but with new external IDs.
    # This will cause the sync_users_with_coops_pt_backend command to fail.
    # This commands fetches the new external IDs and use the member numbers and email addresses
    # to match them to existing members and accounts

    def handle(self, *args, **options):
        with transaction.atomic():
            self.update_share_owner_external_ids()
            self.update_tapir_user_external_ids()

    @classmethod
    def update_share_owner_external_ids(cls):
        share_owners_by_member_number = {
            share_owner.id: share_owner for share_owner in ShareOwner.objects.all()
        }

        response = CoopsPtRequestHandler.get("members?_search=")
        # See tapir.rizoma.management.commands.sync_users_with_coops_pt_backend.Command.sync_members
        # for a reference of the response's content
        if response.status_code != 200:
            raise CoopsPtRequestException("Failed to get user list from coops.pt")
        response_content = response.json()

        for share_owner_json in response_content["data"]:
            if (
                share_owner_json["_deleted_at"] is not None
                or share_owner_json["_firstEmail"] is None
                or share_owner_json["_isActiveSince"] is None
            ):
                continue

            member_number = share_owner_json["number"]
            if member_number not in share_owners_by_member_number:
                print(
                    f"Member with number {member_number} doesn't exist yet, it will be created with the next sync."
                )
                print(f"\tCoops.pt ID: {share_owner_json['_id']}")
                continue

            share_owners_by_member_number[member_number].external_id = share_owner_json[
                "_id"
            ]

        ShareOwner.objects.bulk_update(
            share_owners_by_member_number.values(), ["external_id"]
        )

    @classmethod
    def update_tapir_user_external_ids(cls):
        tapir_users_by_mail_address = {
            tapir_user.email: tapir_user for tapir_user in TapirUser.objects.all()
        }

        response = CoopsPtRequestHandler.get("users?_search=")
        # See tapir.rizoma.management.commands.sync_users_with_coops_pt_backend.Command.sync_users
        # for a reference of the response's content
        if response.status_code != 200:
            raise CoopsPtRequestException("Failed to get user list from coops.pt")
        response_content = response.json()

        for user_json in response_content["data"]:
            if user_json.get("_deleted_at", None) is not None:
                continue

            email_address = user_json["email"]
            if email_address not in tapir_users_by_mail_address.keys():
                print(
                    f"Account with email {email_address} doesn't exist yet, it will be created with the next sync."
                )
                print(f"\tCoops.pt ID: {user_json['_id']}")
                continue

            tapir_users_by_mail_address[email_address].external_id = user_json["_id"]

        TapirUser.objects.bulk_update(
            tapir_users_by_mail_address.values, ["external_id"]
        )

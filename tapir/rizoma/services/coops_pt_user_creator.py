import datetime

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.rizoma.exceptions import CoopsPtRequestException
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler


class CoopsPtUserCreator:
    # Example user json from the coops.pt API:
    #  {'data': {'_created_at': '2025-06-17T10:03:33.387Z',
    #       '_deleted_at': None,
    #       '_id': '332fc8ab-79e2-4446-9464-90ff9d31c9d6',
    #       '_memberName': None,
    #       '_updated_at': '2025-06-20T11:06:42.967Z',
    #       'email': 'devanfisher@lowe.biz',
    #       'firstName': 'Abe',
    #       'lastName': 'Hoppe',
    #       'memberId': None,
    #       'recover_string': None,
    #       'suspended': False,
    #       'type': 'member'},
    #  'meta': {}}

    @classmethod
    def build_tapir_user_from_api_response(cls, user_json: dict) -> TapirUser:
        return TapirUser(
            date_joined=datetime.datetime.fromisoformat(user_json["_created_at"]),
            username=user_json["email"],
            email=user_json["email"],
            first_name=user_json["firstName"],
            last_name=user_json["lastName"],
            preferred_language="pt",
            external_id=user_json["_id"],
            is_superuser=user_json["type"] == "admin",
        )

    @classmethod
    def fetch_and_create_share_owner(cls, external_member_id, tapir_user):
        share_owner = ShareOwner.objects.filter(external_id=external_member_id).first()
        if share_owner is not None:
            if tapir_user.external_id != share_owner.user.external_id:
                share_owner.user = tapir_user
                share_owner.save()
            return

        response = CoopsPtRequestHandler.get(
            url=f"members/{external_member_id}",
        )
        if response.status_code != 200:
            raise CoopsPtRequestException(
                f"Failed to get member data with external ID {external_member_id}"
            )

        member_number = response.json()["data"]["number"]

        ShareOwner.objects.create(
            id=member_number, user=tapir_user, external_id=external_member_id
        )

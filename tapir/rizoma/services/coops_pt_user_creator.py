import datetime

import jwt
import requests
from django.conf import settings

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.rizoma.services.coops_pt_login_manager import CoopsPtLoginManager
from tapir.utils.expection_utils import TapirException


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

        success, access_token, refresh_token = CoopsPtLoginManager.remote_login(
            email=settings.COOPS_PT_ADMIN_EMAIL,
            password=settings.COOPS_PT_ADMIN_PASSWORD,
        )
        if not success:
            raise TapirException(
                "Failed to login as admin in order to to get member data"
            )

        response = requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/members/{external_member_id}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )

        member_number = response.json()["data"]["number"]

        ShareOwner.objects.create(
            id=member_number, user=tapir_user, external_id=external_member_id
        )

    @classmethod
    def get_external_user_id_from_access_token(cls, access_token: str) -> str:
        # Expected format after decoding the access token:
        # {'CustomUserInfo': {'ID': '2372b571-10e8-45e7-9579-0095dc87566e',
        #  'Name': 'admin',
        #  'Role': 'admin'},
        #  'exp': 1749649873,
        #  'iat': 1749648973,
        #  'iss': 'admin'}

        token_data = jwt.decode(
            access_token,
            algorithms=["RS256"],
            options={"verify_signature": True},
            key=settings.RSA_PUBLIC_KEY_DEMO_COOPS_PT,
        )

        return token_data["CustomUserInfo"]["ID"]

    @classmethod
    def get_role_from_access_token(cls, access_token: str) -> str:
        token_data = jwt.decode(
            access_token,
            algorithms=["RS256"],
            options={"verify_signature": True},
            key=settings.RSA_PUBLIC_KEY_DEMO_COOPS_PT,
        )

        return token_data["CustomUserInfo"]["Role"]

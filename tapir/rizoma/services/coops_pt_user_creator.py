import datetime

import jwt

from tapir.accounts.models import TapirUser


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
            algorithms=["HS256"],
            options={"verify_signature": False},
        )

        return token_data["CustomUserInfo"]["ID"]

    @classmethod
    def get_role_from_access_token(cls, access_token: str) -> str:
        token_data = jwt.decode(
            access_token,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )

        return token_data["CustomUserInfo"]["Role"]

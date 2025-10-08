import jwt
from django.conf import settings

from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler


class CoopsPtLoginManager:

    @classmethod
    def remote_login(cls, email, password):
        response = CoopsPtRequestHandler.post(
            url="auth", data={"email": email, "password": password}
        )
        if response.status_code != 200:
            return False, None, None

        response_content = response.json()
        access_token = response_content.get("access", None)
        cls.validate_and_decode_token(access_token)
        refresh_token = response_content.get("refresh", None)
        cls.validate_and_decode_token(refresh_token)

        return True, access_token, refresh_token

    @classmethod
    def validate_and_decode_token(cls, token):
        return jwt.decode(
            token,
            algorithms=["RS256"],
            options={"verify_signature": True},
            key=cls.get_rsa_public_key(),
        )

    @classmethod
    def get_rsa_public_key(cls):
        return settings.COOPS_PT_RSA_PUBLIC_KEY

    @classmethod
    def get_external_user_id_from_access_token(cls, access_token: str) -> str:
        # Expected format after decoding the access token:
        # {'CustomUserInfo': {'ID': '2372b571-10e8-45e7-9579-0095dc87566e',
        #  'Name': 'admin',
        #  'Role': 'admin'},
        #  'exp': 1749649873,
        #  'iat': 1749648973,
        #  'iss': 'admin'}
        token_data = CoopsPtLoginManager.validate_and_decode_token(access_token)

        return token_data["CustomUserInfo"]["ID"]

    @classmethod
    def get_role_from_access_token(cls, access_token: str) -> str:
        token_data = CoopsPtLoginManager.validate_and_decode_token(access_token)

        return token_data["CustomUserInfo"]["Role"]

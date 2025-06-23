import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import BadRequest
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator
from tapir.utils.expection_utils import TapirException


class CoopsPtAuthBackend(BaseBackend):
    def get_user(self, user_id):
        return TapirUser.objects.get(id=user_id)

    def authenticate(self, request, **kwargs):
        email = kwargs.get("email", None)
        if email is None:
            email = kwargs.get("username", None)
        if email is None:
            raise BadRequest(f"Missing 'email' parameter")

        password = kwargs.get("password", None)
        if password is None:
            raise BadRequest(f"Missing 'password' parameter")

        success, access_token, refresh_token = self.remote_login(
            email=email, password=password
        )
        if not success:
            messages.info(request, _("Invalid username or password"))
            return None

        if access_token is None or refresh_token is None:
            messages.error(
                request,
                _("Login system error, please try again later or contact an admin."),
            )
            return None

        user = TapirUser.objects.filter(email=email).first()

        if user is not None:
            self.update_admin_status(user, access_token)
            return user

        external_user_id = CoopsPtUserCreator.get_external_user_id_from_access_token(
            access_token
        )

        response = requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/users/{external_user_id}",  # the request fails if the search param is missing
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            raise TapirException(
                f"Failed to get user from external API, error: '{response.status_code}' '{response.text}'"
            )

        user_data = response.json()["data"]

        with transaction.atomic():
            tapir_user = CoopsPtUserCreator.build_tapir_user_from_api_response(
                user_data
            )
            tapir_user.save()
            self.create_share_owner(user_data["memberId"], tapir_user)

        if user_data["memberId"] is not None:
            pass

        return tapir_user

    @staticmethod
    def remote_login(email, password):
        response = requests.post(
            url=f"{settings.COOPS_PT_API_BASE_URL}/auth",
            headers={"Accept": "application/json"},
            data=f'{{"email": "{email}", "password": "{password}"}}',
        )
        if response.status_code != 200:
            return False, None, None

        response_content = response.json()
        access_token = response_content.get("access", None)
        refresh_token = response_content.get("refresh", None)
        return True, access_token, refresh_token

    @classmethod
    def update_admin_status(cls, user: TapirUser, access_token):
        role = CoopsPtUserCreator.get_role_from_access_token(access_token)
        should_be_admin = role == "admin"

        if should_be_admin == user.is_superuser:
            return

        user.is_superuser = should_be_admin
        user.save()

    @classmethod
    def create_share_owner(cls, external_member_id, tapir_user):
        success, access_token, refresh_token = cls.remote_login(
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

        ShareOwner.objects.create(id=member_number, user=tapir_user)

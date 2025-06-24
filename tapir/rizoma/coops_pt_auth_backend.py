import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import BadRequest
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.rizoma.services.coops_pt_login_manager import CoopsPtLoginManager
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator
from tapir.utils.expection_utils import TapirException


class CoopsPtAuthBackend(BaseBackend):
    def get_user(self, user_id):
        return TapirUser.objects.filter(id=user_id).first()

    def authenticate(self, request, **kwargs):
        email = kwargs.get("email", None)
        if email is None:
            email = kwargs.get("username", None)
        if email is None:
            raise BadRequest(f"Missing 'email' parameter")

        password = kwargs.get("password", None)
        if password is None:
            raise BadRequest(f"Missing 'password' parameter")

        success, access_token, refresh_token = CoopsPtLoginManager.remote_login(
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

        external_user_id = CoopsPtUserCreator.get_external_user_id_from_access_token(
            access_token
        )

        user = TapirUser.objects.filter(external_id=external_user_id).first()

        if user is not None:
            if self.update_admin_status(
                user, role=CoopsPtUserCreator.get_role_from_access_token(access_token)
            ):
                user.save()
            return user

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
            external_member_id = user_data["memberId"]
            if external_member_id is not None:
                CoopsPtUserCreator.fetch_and_create_share_owner(
                    external_member_id, tapir_user
                )

        if user_data["memberId"] is not None:
            pass

        return tapir_user

    @classmethod
    def update_admin_status(cls, user: TapirUser, role):
        should_be_admin = role == "admin"

        if should_be_admin == user.is_superuser:
            return False

        user.is_superuser = should_be_admin
        return True

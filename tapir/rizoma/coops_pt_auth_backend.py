import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
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

        access_token, refresh_token = self.remote_login(
            email=email, password=password, request=request
        )
        if access_token is None or refresh_token is None:
            raise TapirException("Invalid response from login server")

        user = TapirUser.objects.filter(email=email).first()

        if user is not None:
            return user

        external_user_id = CoopsPtUserCreator.get_external_user_id_from_access_token(
            access_token
        )

        response = requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/members/{external_user_id}",  # the request fails if the search param is missing
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            raise TapirException(
                "Failed to get user from external API, error: " + response.text
            )

        tapir_user = CoopsPtUserCreator.build_tapir_user_from_api_response(
            response.json()
        )
        tapir_user.save()

        return tapir_user

    @staticmethod
    def remote_login(email, password, request):
        response = requests.post(
            url=f"{settings.COOPS_PT_API_BASE_URL}/auth",
            headers={"Accept": "application/json"},
            data=f'{{"email": "{email}", "password": "{password}"}}',
        )
        if response.status_code != 200:
            messages.info(request, _("Invalid username or password"))
            return None

        response_content = response.json()
        access_token = response_content.get("access", None)
        refresh_token = response_content.get("refresh", None)
        return access_token, refresh_token

import requests
from django.conf import settings


class CoopsPtLoginManager:
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

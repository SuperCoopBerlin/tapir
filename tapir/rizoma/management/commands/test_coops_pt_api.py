import jwt
import requests
from django.core.management import BaseCommand
from icecream import ic


class Command(BaseCommand):

    def handle(self, *args, **options):
        login_as_admin = True
        if login_as_admin:
            email = "admin@example.com"
            password = "adminPassw0rd"
        else:
            email = "uriahkunde@mante.org"
            password = "uriahkunde@mante.org"
        response = requests.post(
            url="https://api.demo.coops.pt/auth",
            headers={"Accept": "application/json"},
            data=f'{{"email": "{email}", "password": "{password}"}}',
        )
        if response.status_code != 200:
            ic("Login failed", response.status_code, response.text)
            return

        response_content = response.json()
        access_token = response_content.get("access", None)
        refresh_token = response_content.get("refresh", None)

        ic(
            jwt.decode(
                access_token,
                algorithms=["HS256"],
                options={"verify_signature": False},
            )
        )
        return
        response = requests.get(
            url="https://api.demo.coops.pt/members?_search=",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            ic("Request failed", response.status_code, response.text)
            return

        ic(response.text, response.json())

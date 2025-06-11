import requests
from django.conf import settings
from django.core.management import BaseCommand
from icecream import ic

from tapir.accounts.models import TapirUser
from tapir.rizoma.services.coops_pt_user_creator import CoopsPtUserCreator
from tapir.utils.expection_utils import TapirException


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.post(
            url=f"{settings.COOPS_PT_API_BASE_URL}/auth",
            headers={"Accept": "application/json"},
            data=f'{{"email": "{settings.COOPS_PT_ADMIN_EMAIL}", "password": "{settings.COOPS_PT_ADMIN_PASSWORD}"}}',
        )
        if response.status_code != 200:
            raise TapirException(
                "Failed to login to coops.pt with admin credentials from settings"
            )

        response_content = response.json()
        access_token = response_content.get("access", None)

        response = requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/members?_search=",  # the request fails if the search param is missing
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            raise TapirException("Failed to get user list from coops.pt")

        # Example element from the response.data list:
        # {'_created_at': '2025-05-27T15:44:47.514Z',
        #  '_currentState': None,
        #  '_currentStateDate': None,
        #  '_deleted_at': None,
        #  '_firstEmail': None,
        #  '_firstMobile': '9637973395',
        #  '_firstPhone': None,
        #  '_fullAddress': 'Travessa dos Girassóis<br/>84565',
        #  '_id': 'ff758a55-5169-41e6-bd9c-d59905370056',
        #  '_isActiveSince': None,
        #  '_photoId': None,
        #  '_updated_at': '2025-05-27T15:45:20.161Z',
        #  'address': 'Travessa dos Girassóis',
        #  'birthday': '1938-06-07T03:11:33Z',
        #  'city': 'Vale das Montanhas',
        #  'countryId': 239,
        #  'educationalQualifications': 'Profound',
        #  'fiscalNumber': '1788219629960569403',
        #  'idCardNumber': '12713805059784738425',
        #  'name': 'Rui Soares',
        #  'nationalityId': 176,
        #  'notes': 'Practically anger horde murder certain few is how down '
        #           'architect rhythm deliberately under here her those '
        #           'already my these several.',
        #  'number': 96,
        #  'occupation': 'Coordinator',
        #  'placeOfBirth': 'Birmingham',
        #  'zip': '84565'}

        response_content = response.json()
        tapir_users = []
        existing_email_addresses = set(
            TapirUser.objects.values_list("email", flat=True)
        )
        for user_json in response_content["data"]:
            email = user_json["_firstEmail"]
            if email in existing_email_addresses:
                continue
            if user_json.get("_deleted_at", None) is not None:
                continue

            tapir_users.append(
                CoopsPtUserCreator.build_tapir_user_from_api_response(user_json)
            )

        created = TapirUser.objects.bulk_create(tapir_users)
        ic("number of created users", len(created))

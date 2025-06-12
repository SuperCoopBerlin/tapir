import datetime

import jwt

from tapir.accounts.models import TapirUser


class CoopsPtUserCreator:
    # Example user json from the coops.pt API:
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

    @classmethod
    def build_tapir_user_from_api_response(cls, user_json: dict) -> TapirUser:
        phone_number = user_json.get("_firstPhone", None)
        if phone_number is None:
            phone_number = ""

        return TapirUser(
            date_joined=datetime.datetime.fromisoformat(user_json["_created_at"]),
            username=user_json["_firstEmail"],
            email=user_json["_firstEmail"],
            phone_number=phone_number,
            street=user_json["address"],
            postcode=user_json["zip"],
            city=user_json["city"],
            birthdate=datetime.datetime.fromisoformat(user_json["birthday"]),
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

import datetime

# Helper class to deal with users generated from https://randomuser.me/
from tapir.utils.user_utils import UserUtils


class JsonUser:
    first_name: str
    last_name: str
    email: str
    phone_number: str
    date_of_birth: datetime.date
    street: str
    street_2: str
    postcode: str
    city: str
    country: str
    date_joined: datetime.date

    def __init__(self, parsed_json):
        self.first_name = parsed_json["name"]["first"]
        self.last_name = parsed_json["name"]["last"]
        self.email = parsed_json["email"]
        self.phone_number = parsed_json["phone"].replace("-", "")

        date_of_birth = parsed_json["dob"]["date"].replace("Z", "")
        self.date_of_birth = datetime.datetime.fromisoformat(date_of_birth).date()

        self.street = (
            parsed_json["location"]["street"]["name"]
            + " "
            + str(parsed_json["location"]["street"]["number"])
        )

        self.street_2 = ""
        self.postcode = str(parsed_json["location"]["postcode"])
        self.city = parsed_json["location"]["city"]
        self.country = parsed_json["location"]["country"]

        date_joined = parsed_json["registered"]["date"].replace("Z", "")
        self.date_joined = datetime.datetime.fromisoformat(date_joined)

    def get_username(self) -> str:
        return UserUtils.build_username(self.first_name, self.last_name)

    def get_display_name(self) -> str:
        return UserUtils.build_display_name(self.first_name, self.last_name)

    def get_date_of_birth_str_for_input_field(self) -> str:
        return self.date_of_birth.strftime("%Y-%m-%d")

    def get_date_of_birth_display(self) -> str:
        return self.date_of_birth.strftime("%d.%m.%Y")

    def get_display_address(self) -> str:
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

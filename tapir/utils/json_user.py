import datetime

# Helper class to deal with users generated from https://randomuser.me/


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
        # TODO Théo 02.05.21
        # Replace special characters like in updateUsername() in tapir/coop/static/coop/js/draftuser_form.js
        return self.first_name.lower() + "_" + self.last_name.lower()

    def get_display_name(self) -> str:
        return self.first_name + " " + self.last_name

    def get_date_of_birth_str_for_input_field(self) -> str:
        return self.date_of_birth.strftime("%Y-%m-%d")

    def get_complete_address(self) -> str:
        result = self.street
        if self.street_2 is not None and len(self.street_2) > 0:
            result += " " + self.street_2
        result += ", " + self.postcode + " " + self.city
        return result

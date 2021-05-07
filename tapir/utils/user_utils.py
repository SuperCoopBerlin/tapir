class UserUtils:
    @staticmethod
    def build_display_name(first_name: str, last_name: str) -> str:
        return first_name + " " + last_name

    @staticmethod
    def build_display_address(
        street: str, street_2: str, postcode: str, city: str
    ) -> str:
        address = street + ", "
        if street_2 is not None and len(street_2) > 0:
            address += street_2 + ", "
        address += postcode + " " + city
        return address

    @staticmethod
    def build_username(first_name: str, last_name: str):
        # TODO Théo 03.05.21 Replace special characters like in updateUsername() in tapir/coop/static/coop/js/draftuser_form.js
        return first_name.lower() + "_" + last_name.lower()

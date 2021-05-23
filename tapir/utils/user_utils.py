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

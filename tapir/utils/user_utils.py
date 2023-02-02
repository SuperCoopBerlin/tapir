from barcode import EAN13
from barcode.writer import SVGWriter


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
    def get_full_street(street: str, street_2: str):
        address = street
        if street_2 is not None and len(street_2) > 0:
            address += ", " + street_2
        return address

    @staticmethod
    def get_member_card_barcode_as_svg(tapir_user) -> str:
        writer = SVGWriter()
        return (
            EAN13(str(tapir_user.share_owner.get_id_for_biooffice()), writer=writer)
            .render(writer_options={"module_width": 0.8, "module_height": 60})
            .decode("utf-8")
        )

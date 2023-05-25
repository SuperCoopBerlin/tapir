from barcode import EAN13
from barcode.writer import SVGWriter

from tapir import settings
from tapir.utils.shortcuts import get_html_link


class UserUtils:
    DISPLAY_NAME_TYPE_FULL = "full"
    DISPLAY_NAME_TYPE_SHORT = "short"

    @staticmethod
    def build_display_name(first_name: str, last_name: str) -> str:
        return first_name + " " + last_name

    @classmethod
    def build_company_name(cls):
        pass

    @classmethod
    def build_display_name_2(cls, person, display_type: str):
        person = person.get_info()
        display_name = person.usage_name if person.usage_name else person.first_name

        if display_type == cls.DISPLAY_NAME_TYPE_FULL:
            display_name = f"{display_name} {person.last_name}"
            if person.get_member_number():
                display_name = f"{display_name} #{person.get_member_number()}"

        return display_name

    @classmethod
    def build_display_name_for_viewer(cls, person, viewer):
        display_type = cls.DISPLAY_NAME_TYPE_SHORT
        if viewer and (
            viewer.has_perm(settings.PERMISSION_COOP_VIEW)
            or viewer.has_perm(settings.PERMISSION_ACCOUNTS_VIEW)
        ):
            display_type = cls.DISPLAY_NAME_TYPE_FULL
        return cls.build_display_name_2(person, display_type)

    @classmethod
    def build_html_link_for_viewer(cls, person, viewer):
        return get_html_link(
            url=person.get_absolute_url(),
            text=cls.build_display_name_for_viewer(person, viewer),
        )

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

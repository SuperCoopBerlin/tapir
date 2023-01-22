import phonenumbers
from barcode import EAN13
from barcode.writer import SVGWriter
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from phonenumbers import PhoneNumberFormat

from tapir.coop.models import ShareOwner

register = template.Library()


@register.filter
@stringfilter
def format_phone_number(phone_number):
    return (
        phonenumbers.format_number(
            phonenumbers.parse(
                number=phone_number, region=settings.PHONENUMBER_DEFAULT_REGION
            ),
            PhoneNumberFormat.INTERNATIONAL,
        )
        if phone_number
        else ""
    )


@register.inclusion_tag("accounts/member_card_barcode.html", takes_context=True)
def member_card_barcode(context, share_owner: ShareOwner):
    writer = SVGWriter()
    context["barcode_as_svg"] = (
        EAN13(str(share_owner.get_id_for_biooffice()), writer=writer)
        .render(writer_options={"module_width": 0.6, "module_height": 45})
        .decode("utf-8")
    )
    return context

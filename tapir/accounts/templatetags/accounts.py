import phonenumbers
from barcode import EAN13
from barcode.writer import SVGWriter
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from phonenumbers import PhoneNumberFormat

from tapir.accounts.models import TapirUser

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


@register.inclusion_tag("accounts/purchase_tracking_card.html", takes_context=True)
def purchase_tracking_card(context, tapir_user: TapirUser):
    writer = SVGWriter()
    if not tapir_user.share_owner:
        return context

    context["barcode_as_svg"] = (
        EAN13(str(tapir_user.share_owner.get_id_for_biooffice()), writer=writer)
        .render(writer_options={"module_width": 0.8, "module_height": 60})
        .decode("utf-8")
    )
    context["tapir_user"] = tapir_user
    return context

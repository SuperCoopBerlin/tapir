import phonenumbers
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from phonenumbers import PhoneNumberFormat, PhoneNumber

register = template.Library()


@register.filter
@stringfilter
def format_phone_number(phone_number):
    return phonenumbers.format_number(
        phonenumbers.parse(
            number=phone_number, region=settings.PHONENUMBER_DEFAULT_REGION
        ),
        PhoneNumberFormat.INTERNATIONAL,
    )

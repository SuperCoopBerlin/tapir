import phonenumbers
from django import template
from django.template.defaultfilters import stringfilter
from phonenumbers import PhoneNumberFormat, PhoneNumber

register = template.Library()


@register.filter
@stringfilter
def format_phone_number(phone_number):
    return phonenumbers.format_number(
        phonenumbers.parse(phone_number), PhoneNumberFormat.INTERNATIONAL
    )

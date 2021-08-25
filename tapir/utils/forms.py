from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget


class DateInput(forms.DateInput):
    input_type = "date"

    def format_value(self, value: date):
        return value.strftime("%Y-%m-%d")


class TapirPhoneNumberField(PhoneNumberField):

    widget = PhoneNumberInternationalFallbackWidget

    def __init__(self, *args, **kwargs):
        help_text = _(
            "German phone number don't need a prefix (e.g. (0)1736160646), international always (e.g. +12125552368)"
        )
        super(TapirPhoneNumberField, self).__init__(
            *args, help_text=help_text, **kwargs
        )

from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget


class DateInput(forms.DateInput):
    input_type = "date"


class TapirPhoneNumberField(PhoneNumberField):

    widget = PhoneNumberInternationalFallbackWidget

    def __init__(self, *args, **kwargs):
        help_text = _(
            "German phone number don't need a prefix (e.g. (0)1736160646), international always (e.g. +12125552368)"
        )
        super(TapirPhoneNumberField, self).__init__(
            *args, help_text=help_text, **kwargs
        )


class UserInfoFormMixin:
    def clean_field(self: forms.ModelForm, field_name: str):
        return self.cleaned_data.get(field_name, "").strip()

    def clean_first_name(self):
        return self.clean_field("first_name")

    def clean_last_name(self):
        return self.clean_field("last_name")

    def clean_street(self):
        return self.clean_field("street")

    def clean_street_2(self):
        return self.clean_field("street_2")

    def clean_postcode(self):
        return self.clean_field("postcode")

    def clean_city(self):
        return self.clean_field("city")

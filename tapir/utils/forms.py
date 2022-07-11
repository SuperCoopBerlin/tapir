from datetime import date

from django import forms
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_filters import RangeFilter
from django_filters.fields import DateRangeField
from django_filters.widgets import DateRangeWidget, SuffixedMultiWidget
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget


class DateInputTapir(forms.DateInput):
    input_type = "date"

    def format_value(self, value: date):
        return formats.localize_input(value, "%Y-%m-%d")


class TapirPhoneNumberField(PhoneNumberField):

    widget = PhoneNumberInternationalFallbackWidget

    def __init__(self, *args, **kwargs):
        help_text = _(
            "German phone number don't need a prefix (e.g. (0)1736160646), international always (e.g. +12125552368)"
        )
        super(TapirPhoneNumberField, self).__init__(
            *args, help_text=help_text, **kwargs
        )


class DateRangeWidgetTapir(DateRangeWidget):
    suffixes = ["after", "before"]

    def __init__(self, attrs=None):
        widgets = (DateInputTapir, DateInputTapir)
        super(SuffixedMultiWidget, self).__init__(widgets, attrs)


class DateRangeFieldTapir(DateRangeField):
    widget = DateRangeWidgetTapir


class DateFromToRangeFilterTapir(RangeFilter):
    field_class = DateRangeFieldTapir

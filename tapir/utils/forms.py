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
            "German phone numbers don't need a prefix (e.g. (0)1736160646), international always (e.g. +12125552368)"
        )
        super(TapirPhoneNumberField, self).__init__(
            *args, help_text=help_text, **kwargs
        )


class DateRangeWidgetTapir(DateRangeWidget):
    suffixes = ["start", "end"]

    def __init__(self, attrs=None):
        start = DateInputTapir(attrs={"aria_label": "end date"})
        end = DateInputTapir(attrs={"aria_label": "end date"})
        widgets = (start, end)
        super(SuffixedMultiWidget, self).__init__(widgets, attrs)


class DateRangeFieldTapir(DateRangeField):
    widget = DateRangeWidgetTapir


class DateFromToRangeFilterTapir(RangeFilter):
    field_class = DateRangeFieldTapir
